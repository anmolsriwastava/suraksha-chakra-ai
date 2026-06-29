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

# Lazy load langchain inside the class to prevent slow module-level imports
# that cause Render port timeouts.

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





class WageEngine:
    def __init__(self):
        from langchain_groq import ChatGroq
        
        self.vector_store = None
        self.qa_chain = None
        self.embeddings = None  # Disabled to prevent PyTorch OOM on Render
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
        # FAISS and PyTorch are disabled for the Render deployment because they
        # exceed the 512MB RAM limit and cause silent OOM crashes.
        # We rely exclusively on the deterministic BOCW_WAGES lookup table.
        logger.info("FAISS index building disabled to save RAM. Using exact lookup only.")
        self.vector_store = None
        self.qa_chain = None
        logger.info("Wage engine ready (Lookup mode).")

    def _load_all_pdfs(self) -> list:
        """
        Walk data/raw/ and load every PDF we find.
        Returns a flat list of LangChain Document objects.
        """
        from langchain_community.document_loaders import PyPDFLoader
        
        raw_dir = Path(settings.raw_data_dir)
        all_docs = []

        pdf_files = list(raw_dir.glob("**/*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDFs found in {raw_dir}. Index will be empty.")
            return []

        for pdf_path in pdf_files:
            logger.info(f"Loading {pdf_path.name}...")
            try:
                loader = PyPDFLoader(str(pdf_path))
                docs = loader.load()
                # tag each doc with its source file
                for doc in docs:
                    doc.metadata["source_file"] = pdf_path.stem
                all_docs.extend(docs)
            except Exception as e:
                # skip corrupt PDFs, don't crash everything
                logger.error(f"Failed to load {pdf_path.name}: {e}")

        return all_docs

    def _split_into_chunks(self, documents: list) -> list:
        """
        Split docs into chunks suitable for embedding.
        Smaller chunks = more precise retrieval for wage tables.
        """
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
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
        from langchain_community.vectorstores import FAISS
        
        documents = self._load_all_pdfs()

        if not documents:
            # create a dummy index with some hardcoded wages as fallback
            logger.warning("Using hardcoded fallback wage data.")
            self.vector_store = self._build_fallback_index()
            return

        chunks = self._split_into_chunks(documents)
        
        if not chunks:
            logger.info("No chunks to embed. Creating empty fallback index.")
            self.vector_store = self._build_fallback_index()
        else:
            logger.info(f"Embedding {len(chunks)} chunks using HuggingFace...")
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)

        # save so we don't re-embed on every restart
        self._embeddings_path.mkdir(parents=True, exist_ok=True)
        self.vector_store.save_local(str(self._embeddings_path))
        logger.info(f"Index saved to {self._embeddings_path}")

    def _build_fallback_index(self):
        from langchain_core.documents import Document
        from langchain_community.vectorstores import FAISS
        
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
        from langchain_classic.chains import RetrievalQA
        from langchain_core.prompts import PromptTemplate
        
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

    # ── Direct lookup table ──────────────────────────────────────────
    # Deterministic wage data from BOCW schedules — no LLM randomness.
    # Format: (state_lower, occupation_lower) → (wage_per_day)
    BOCW_WAGES = {
        # Delhi
        ("delhi", "mason"): 730, ("delhi", "electrician"): 756,
        ("delhi", "plumber"): 730, ("delhi", "carpenter"): 730,
        ("delhi", "painter"): 700, ("delhi", "helper"): 589,
        ("delhi", "welder"): 756, ("delhi", "driver"): 689,
        # Maharashtra
        ("maharashtra", "mason"): 650, ("maharashtra", "electrician"): 720,
        ("maharashtra", "plumber"): 700, ("maharashtra", "carpenter"): 660,
        ("maharashtra", "painter"): 630, ("maharashtra", "helper"): 500,
        ("maharashtra", "welder"): 720, ("maharashtra", "driver"): 620,
        # Mumbai → Maharashtra
        ("mumbai", "mason"): 650, ("mumbai", "electrician"): 720,
        ("mumbai", "plumber"): 700, ("mumbai", "carpenter"): 660,
        ("mumbai", "painter"): 630, ("mumbai", "helper"): 500,
        ("mumbai", "welder"): 720, ("mumbai", "driver"): 620,
        # Uttar Pradesh
        ("uttar pradesh", "mason"): 531, ("uttar pradesh", "electrician"): 583,
        ("uttar pradesh", "plumber"): 560, ("uttar pradesh", "carpenter"): 540,
        ("uttar pradesh", "painter"): 520, ("uttar pradesh", "helper"): 428,
        ("uttar pradesh", "welder"): 583, ("uttar pradesh", "driver"): 480,
        ("up", "mason"): 531, ("up", "electrician"): 583,
        ("up", "plumber"): 560, ("up", "carpenter"): 540,
        ("up", "painter"): 520, ("up", "helper"): 428,
        ("up", "welder"): 583, ("up", "driver"): 480,
        # Bihar
        ("bihar", "mason"): 494, ("bihar", "electrician"): 543,
        ("bihar", "plumber"): 520, ("bihar", "carpenter"): 505,
        ("bihar", "painter"): 490, ("bihar", "helper"): 393,
        ("bihar", "welder"): 543, ("bihar", "driver"): 450,
        # Gujarat
        ("gujarat", "mason"): 613, ("gujarat", "electrician"): 674,
        ("gujarat", "plumber"): 650, ("gujarat", "carpenter"): 625,
        ("gujarat", "painter"): 600, ("gujarat", "helper"): 490,
        ("gujarat", "welder"): 674, ("gujarat", "driver"): 570,
        # Rajasthan
        ("rajasthan", "mason"): 521, ("rajasthan", "electrician"): 573,
        ("rajasthan", "plumber"): 550, ("rajasthan", "carpenter"): 530,
        ("rajasthan", "painter"): 510, ("rajasthan", "helper"): 415,
        ("rajasthan", "welder"): 573, ("rajasthan", "driver"): 470,
        # West Bengal
        ("west bengal", "mason"): 578, ("west bengal", "electrician"): 635,
        ("west bengal", "plumber"): 610, ("west bengal", "carpenter"): 590,
        ("west bengal", "painter"): 565, ("west bengal", "helper"): 455,
        ("west bengal", "welder"): 635, ("west bengal", "driver"): 530,
        # Karnataka
        ("karnataka", "mason"): 698, ("karnataka", "electrician"): 768,
        ("karnataka", "plumber"): 740, ("karnataka", "carpenter"): 710,
        ("karnataka", "painter"): 680, ("karnataka", "helper"): 543,
        ("karnataka", "welder"): 768, ("karnataka", "driver"): 640,
    }

    def query_fair_wage(self, occupation: str, location: str) -> WageQueryResult:
        """
        Main entry point. Given an occupation and location,
        return the fair wage range from BOCW data.

        Uses deterministic lookup table. RAG is disabled for Render deployment.
        """
        occ_lower = occupation.lower().strip()
        loc_lower = location.lower().strip()

        # Direct lookup (always consistent)
        exact_wage = self.BOCW_WAGES.get((loc_lower, occ_lower))
        if exact_wage:
            return WageQueryResult(
                occupation=occupation,
                location=location,
                fair_wage_min=exact_wage * 0.92,
                fair_wage_max=exact_wage,
                source=f"{location.capitalize()} BOCW Minimum Wage Schedule 2024",
                confidence="high"
            )

        # RAG is disabled to save RAM, return Groq LLM estimate directly
        logger.warning(f"Using LLM fallback for {occupation} in {location} (RAG disabled)")
        
        try:
            query_str = f"What is the minimum or fair wage for a {occupation} in {location} in India? Respond with only JSON: {{\"fair_wage_min\": 400, \"fair_wage_max\": 600, \"source\": \"Estimate\", \"confidence\": \"low\"}}"
            res = self.llm.invoke(query_str)
            raw_text = res.content.strip()
            
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0]
                
            import json
            data = json.loads(raw_text)
            
            return WageQueryResult(
                occupation=occupation,
                location=location,
                fair_wage_min=float(data.get("fair_wage_min", 450)),
                fair_wage_max=float(data.get("fair_wage_max", 700)),
                source=data.get("source", "LLM Estimate"),
                confidence="medium",
            )
        except Exception as e:
            logger.error(f"LLM fallback failed: {e}")
            return WageQueryResult(
                occupation=occupation,
                location=location,
                fair_wage_min=450,
                fair_wage_max=700,
                source="National floor wage estimate",
                confidence="low",
            )


# module-level singleton — initialized once at startup
_wage_engine_instance: WageEngine | None = None


def get_wage_engine() -> WageEngine:
    """FastAPI dependency — returns the initialized singleton."""
    global _wage_engine_instance
    if _wage_engine_instance is None:
        _wage_engine_instance = WageEngine()
        _wage_engine_instance.load_or_build_index()
    return _wage_engine_instance
