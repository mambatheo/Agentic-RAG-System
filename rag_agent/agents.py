import os
from typing import List, Dict
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from .safety import SafetyValidator

class ResearchAssistantAgent:
    """Agentic RAG system - FREE VERSION (No API key required)"""
    
    META_SYSTEM_PROMPT = """You are an AI Research Assistant Agent.

ROLE: Expert research assistant specializing in AI, machine learning, and computer science.

GOALS:
1. Provide accurate answers based on retrieved documents
2. Synthesize information from multiple sources
3. Cite sources when making claims
4. Admit when information is unavailable

CONSTRAINTS:
1. Only use information from retrieved documents
2. Never fabricate facts or citations
3. Flag uncertainties and limitations
4. Maintain academic integrity
5. Avoid speculation beyond sources
6. Never provide harmful information"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        # FREE: Use HuggingFace embeddings (no API key needed)
        print("🔄 Initializing HuggingFace embeddings (first time may take a minute)...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vectorstore = None
        print("✅ Embeddings ready!")
    
    def load_knowledge_base(self, documents_path: str) -> int:
        """Load and index documents"""
        print("📚 Loading documents...")
        documents = []
        for filename in os.listdir(documents_path):
            if filename.endswith('.txt'):
                filepath = os.path.join(documents_path, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    documents.append(f.read())
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        texts = []
        for doc in documents:
            texts.extend(text_splitter.split_text(doc))
        
        print(f"🔄 Creating embeddings for {len(texts)} chunks... (this may take 1-2 minutes)")
        self.vectorstore = Chroma.from_texts(
            texts=texts,
            embedding=self.embeddings,
            persist_directory=self.db_path
        )
        print("✅ Knowledge base loaded successfully!")
        
        return len(texts)
    
    def retrieve_documents(self, query: str, k: int = 4) -> List[str]:
        """Retrieve and validate relevant documents"""
        if not self.vectorstore:
            print("🔄 Loading existing vector database...")
            self.vectorstore = Chroma(
                persist_directory=self.db_path,
                embedding_function=self.embeddings
            )
        
        docs = self.vectorstore.similarity_search(query, k=k)
        doc_texts = [doc.page_content for doc in docs]
        return SafetyValidator.validate_retrieved_docs(doc_texts)
    
    def maker_generate(self, query: str, context: List[str]) -> str:
        """Maker: Generate answer using retrieved context"""
        # Build answer from context
        answer = f"Based on the research documents in the knowledge base:\n\n"
        
        # Add relevant excerpts
        for i, doc in enumerate(context, 1):
            # Get meaningful sentences
            sentences = [s.strip() + '.' for s in doc.split('.') if len(s.strip()) > 20]
            if sentences:
                answer += f"**Source {i}:**\n"
                answer += "\n".join(sentences[:3]) + "\n\n"
        
        # Add summary section
        answer += f"\n**Summary for your query: '{query}'**\n"
        answer += "The documents above contain relevant information addressing your question. "
        answer += "Key concepts include: "
        
        # Extract key terms
        words = ' '.join(context).lower().split()
        key_terms = [w for w in set(words) if len(w) > 8 and w.isalpha()][:5]
        answer += ", ".join(key_terms) + ".\n\n"
        
        answer += "*Note: This response is generated from the local knowledge base using semantic search.*"
        
        return answer
    
    def checker_review(self, query: str, context: List[str], answer: str) -> Dict:
        """Checker: Validate answer quality"""
        issues = []
        
        # Check length
        if len(answer) < 100:
            issues.append("Answer is too short")
        
        # Check if context is referenced
        if "Source" not in answer:
            issues.append("Sources not properly referenced")
        
        # Check if query terms are addressed
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        if len(query_words & answer_words) < 2:
            issues.append("Answer may not fully address the query")
        
        approved = len(issues) == 0
        
        feedback = f"""APPROVED: {"YES" if approved else "NO"}
ISSUES: {", ".join(issues) if issues else "None"}
SUGGESTIONS: {"None" if approved else "Add more context from documents"}"""
        
        return {"approved": approved, "feedback": feedback}
    
    def refine_answer(self, query: str, context: List[str], original_answer: str, feedback: str) -> str:
        """Refine answer based on checker feedback"""
        refined = original_answer + "\n\n**Additional Context:**\n"
        
        # Add more details from context
        for doc in context[:2]:
            sentences = [s.strip() + '.' for s in doc.split('.') if len(s.strip()) > 30]
            if sentences:
                refined += sentences[0] + " "
        
        return refined
    
    def process_query(self, query: str, max_iterations: int = 2) -> Dict:
        """Complete maker-checker pipeline"""
        result = {
            "query": query,
            "is_safe": True,
            "safety_issues": [],
            "iterations": [],
            "final_answer": "",
            "approved": False
        }
        
        # Step 1: Input validation
        is_safe, issues = SafetyValidator.validate_input(query)
        if not is_safe:
            result["is_safe"] = False
            result["safety_issues"] = issues
            result["final_answer"] = "⚠️ Query blocked by safety validation: " + "; ".join(issues)
            return result
        
        # Step 2: Retrieve documents
        try:
            context = self.retrieve_documents(query)
            if not context:
                result["final_answer"] = "No relevant documents found in the knowledge base for this query."
                return result
        except Exception as e:
            result["final_answer"] = f"Error retrieving documents: {str(e)}"
            return result
        
        # Step 3: Maker-Checker loop
        current_answer = None
        for iteration in range(max_iterations):
            if iteration == 0:
                current_answer = self.maker_generate(query, context)
            else:
                current_answer = self.refine_answer(
                    query, 
                    context, 
                    current_answer, 
                    result["iterations"][-1]["checker_feedback"]
                )
            
            review = self.checker_review(query, context, current_answer)
            
            result["iterations"].append({
                "iteration": iteration + 1,
                "maker_answer": current_answer,
                "checker_feedback": review["feedback"],
                "approved": review["approved"]
            })
            
            if review["approved"]:
                result["approved"] = True
                break
        
        # Step 4: Sanitize output
        result["final_answer"] = SafetyValidator.sanitize_output(current_answer or "Unable to generate answer.")
        
        return result