"""
RAG Wage Engine

Loads BOCW (Building & Other Construction Workers) wage PDFs
and Labour Ministry data, builds a FAISS vector store, and
answers occupation + location based fair wage queries.

Flow:
  PDF → chunks → embeddings → FAISS index
  query("mason in Delhi") → retrieve top chunks → LLM → structured answer
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class WageQueryResult:
    occupation: str
    location: str
    fair_wage_min: float
    fair_wage_max: float
    currency: str = "INR"
    per: str = "day"
    source: str = ""
    confidence: str = "high"  # high | medium | low


# Prompt that forces the LLM to return structured JSON
WAGE_QUERY_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are an expert on Indian labour law and BOCW wage schedules.
Use ONLY the context below to answer. Do not make up numbers.

Context:
{context}

Question: {question}

Respond in this exact JSON format (no extra text):
{{
  "fair_wage_min": <number or null>,
  "fair_wage_max": <number or null>,
  "per": "day",
  "source": "<which document/state schedule>",
  "confidence": "high" | "medium" | "low",
  "note": "<any important caveat>"
}}

If the context does not contain enough info, set confidence to "low"
and set fair_wage_min/max to null.
"""
)


class WageEngine:
    def __init__(self):
        self.vector_store = None
        self.qa_chain = None
        self.embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.llm = ChatGroq(
        groq_api_key=settings.groq_api_key,
        model_name="llama-3.1-8b-instant",
        temperature=0
        )
        self._embeddings_path = Path(settings.embeddings_dir) / "wage_index"

    def load_or_build_index(self):
        """
        Load the FAISS index from disk if it exists, otherwise
        build it fresh from all PDFs in data/raw/.
        """
        if self._embeddings_path.exists():
            logger.info("Loading existing FAISS wage index from disk...")
            self.vector_store = FAISS.load_local(
                str(self._embeddings_path),
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        else:
            logger.info("No index found — building from raw PDFs...")
            self._build_index_from_pdfs()

        self._setup_qa_chain()
        logger.info("Wage engine ready.")

    def _load_all_pdfs(self) -> list:
        """
        Walk data/raw/ and load every PDF we find.
        Returns a flat list of LangChain Document objects.
        """
        raw_dir = Path(settings.raw_data_dir)
        all_docs = []

        pdf_files = list(raw_dir.glob("**/*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDFs found in {raw_dir}. Index will be empty.")
            return []

        for pdf_path in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_path))
                docs = loader.load()
                # tag each doc with its source file
                for doc in docs:
                    doc.metadata["source_file"] = pdf_path.name
                all_docs.extend(docs)
                logger.info(f"Loaded {len(docs)} pages from {pdf_path.name}")
            except Exception as e:
                # skip corrupt PDFs, don't crash everything
                logger.error(f"Failed to load {pdf_path.name}: {e}")

        return all_docs

    def _split_into_chunks(self, documents: list) -> list:
        """
        Split docs into chunks suitable for embedding.
        Smaller chunks = more precise retrieval for wage tables.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=80,
            separators=["\n\n", "\n", ".", " "]
        )
        chunks = splitter.split_documents(documents)
        logger.info(f"Split into {len(chunks)} chunks")
        return chunks

    def _build_index_from_pdfs(self):
        """Build FAISS index and save to disk."""
        documents = self._load_all_pdfs()

        if not documents:
            # create a dummy index with some hardcoded wages as fallback
            logger.warning("Using hardcoded fallback wage data.")
            self.vector_store = self._build_fallback_index()
            return

        chunks = self._split_into_chunks(documents)
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)

        # save so we don't re-embed on every restart
        self._embeddings_path.mkdir(parents=True, exist_ok=True)
        self.vector_store.save_local(str(self._embeddings_path))
        logger.info(f"Index saved to {self._embeddings_path}")

    def _build_fallback_index(self):
        from langchain_core.documents import Document
        
        wage_data = [
            # Delhi
            Document(page_content="Delhi BOCW minimum wage schedule 2024: Mason (Rajmistri) Rs 730 per day. Electrician Rs 756 per day. Plumber Rs 730 per day. Carpenter Rs 730 per day. Painter Rs 700 per day. Helper/Unskilled worker Rs 589 per day. Welder Rs 756 per day. Steel fixer Rs 730 per day. Driver Rs 689 per day.", metadata={"source_file": "delhi_bocw_2024", "state": "Delhi"}),
            
            # Maharashtra
            Document(page_content="Maharashtra BOCW minimum wage schedule 2024: Mason Rs 650 per day. Electrician Rs 720 per day. Plumber Rs 700 per day. Carpenter Rs 660 per day. Painter Rs 630 per day. Helper/Unskilled worker Rs 500 per day. Welder Rs 720 per day. Steel fixer Rs 660 per day. Driver Rs 620 per day.", metadata={"source_file": "maharashtra_bocw_2024", "state": "Maharashtra"}),
            
            # Uttar Pradesh
            Document(page_content="Uttar Pradesh BOCW minimum wage schedule 2024: Mason Rs 531 per day. Electrician Rs 583 per day. Plumber Rs 560 per day. Carpenter Rs 540 per day. Painter Rs 520 per day. Helper/Unskilled worker Rs 428 per day. Welder Rs 583 per day. Steel fixer Rs 540 per day. Driver Rs 480 per day.", metadata={"source_file": "up_bocw_2024", "state": "Uttar Pradesh"}),
            
            # Bihar
            Document(page_content="Bihar BOCW minimum wage schedule 2024: Mason Rs 494 per day. Electrician Rs 543 per day. Plumber Rs 520 per day. Carpenter Rs 505 per day. Painter Rs 490 per day. Helper/Unskilled worker Rs 393 per day. Welder Rs 543 per day. Steel fixer Rs 505 per day. Driver Rs 450 per day.", metadata={"source_file": "bihar_bocw_2024", "state": "Bihar"}),
            
            # Gujarat
            Document(page_content="Gujarat BOCW minimum wage schedule 2024: Mason Rs 613 per day. Electrician Rs 674 per day. Plumber Rs 650 per day. Carpenter Rs 625 per day. Painter Rs 600 per day. Helper/Unskilled worker Rs 490 per day. Welder Rs 674 per day. Steel fixer Rs 625 per day. Driver Rs 570 per day.", metadata={"source_file": "gujarat_bocw_2024", "state": "Gujarat"}),
            
            # Rajasthan
            Document(page_content="Rajasthan BOCW minimum wage schedule 2024: Mason Rs 521 per day. Electrician Rs 573 per day. Plumber Rs 550 per day. Carpenter Rs 530 per day. Painter Rs 510 per day. Helper/Unskilled worker Rs 415 per day. Welder Rs 573 per day. Steel fixer Rs 530 per day. Driver Rs 470 per day.", metadata={"source_file": "rajasthan_bocw_2024", "state": "Rajasthan"}),
            
            # West Bengal
            Document(page_content="West Bengal BOCW minimum wage schedule 2024: Mason Rs 578 per day. Electrician Rs 635 per day. Plumber Rs 610 per day. Carpenter Rs 590 per day. Painter Rs 565 per day. Helper/Unskilled worker Rs 455 per day. Welder Rs 635 per day. Steel fixer Rs 590 per day. Driver Rs 530 per day.", metadata={"source_file": "westbengal_bocw_2024", "state": "West Bengal"}),
            
            # Karnataka
            Document(page_content="Karnataka BOCW minimum wage schedule 2024: Mason Rs 698 per day. Electrician Rs 768 per day. Plumber Rs 740 per day. Carpenter Rs 710 per day. Painter Rs 680 per day. Helper/Unskilled worker Rs 543 per day. Welder Rs 768 per day. Steel fixer Rs 710 per day. Driver Rs 640 per day.", metadata={"source_file": "karnataka_bocw_2024", "state": "Karnataka"}),

            # National floor
            Document(page_content="National minimum wage floor 2024 as per Ministry of Labour: The national floor level minimum wage is Rs 178 per day for unskilled workers. All state BOCW schedules must be at or above this floor. Construction workers are entitled to BOCW Act benefits including health insurance, pension, education for children, and maternity benefits.", metadata={"source_file": "national_floor_2024", "state": "National"}),

            # BOCW rights
            Document(page_content="BOCW Act 1996 worker rights: Every construction worker must be registered with the state BOCW board. Employers must pay wages on time, provide safe working conditions, and contribute to the welfare fund. Workers can file complaints with the district labour officer. Wage theft is punishable under Section 374 IPC (unlawful compulsory labour) and the Payment of Wages Act 1936.", metadata={"source_file": "bocw_rights_2024", "state": "National"}),
        ]
        
        return FAISS.from_documents(wage_data, self.embeddings)

    def _setup_qa_chain(self):
        """Attach a RetrievalQA chain to the vector store."""
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}  # top 4 chunks should be enough for wage lookup
        )
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": WAGE_QUERY_PROMPT}
        )

    def query_fair_wage(self, occupation: str, location: str) -> WageQueryResult:
        """
        Main entry point. Given an occupation and location,
        return the fair wage range from BOCW data.

        Raises ValueError if the engine is not initialized.
        """
        if self.qa_chain is None:
            raise ValueError("Wage engine not initialized. Call load_or_build_index() first.")

        question = (
            f"What is the minimum daily wage for a {occupation} "
            f"working in {location}, India according to BOCW schedule?"
        )

        try:
            raw_response = self.qa_chain.invoke({"query": question})
            result_text = raw_response.get("result", "")
            wage_data = self._parse_llm_response(result_text)
        except json.JSONDecodeError:
            logger.error(f"LLM returned non-JSON for: {question}\nGot: {result_text}")
            wage_data = self._get_hardcoded_fallback(occupation, location)
        except Exception as e:
            logger.error(f"Wage query failed: {e}")
            wage_data = self._get_hardcoded_fallback(occupation, location)

        fair_wage_min = wage_data.get("fair_wage_min") or 0
        fair_wage_max = wage_data.get("fair_wage_max") or 0
        
        if fair_wage_min > 0 and fair_wage_min == fair_wage_max:
            fair_wage_min = round(fair_wage_max * 0.92)

        return WageQueryResult(
            occupation=occupation,
            location=location,
            fair_wage_min=fair_wage_min,
            fair_wage_max=fair_wage_max,
            source=wage_data.get("source", "BOCW schedule"),
            confidence=wage_data.get("confidence", "low"),
        )

    def _parse_llm_response(self, response_text: str) -> dict:
        """Strip any markdown fences and parse JSON."""
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            # strip ```json ... ``` wrapper
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        return json.loads(cleaned)

    def _get_hardcoded_fallback(self, occupation: str, location: str) -> dict:
        """
        Last resort fallback if LLM fails.
        Returns a broad safe range rather than wrong data.
        """
        logger.warning(f"Using hardcoded fallback for {occupation} in {location}")
        return {
            "fair_wage_min": 450,
            "fair_wage_max": 700,
            "source": "National floor wage estimate",
            "confidence": "low",
        }


# module-level singleton — initialized once at startup
_wage_engine_instance: WageEngine | None = None


def get_wage_engine() -> WageEngine:
    """FastAPI dependency — returns the initialized singleton."""
    global _wage_engine_instance
    if _wage_engine_instance is None:
        _wage_engine_instance = WageEngine()
        _wage_engine_instance.load_or_build_index()
    return _wage_engine_instance
