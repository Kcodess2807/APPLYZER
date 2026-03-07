"""LangGraph workflow for human-in-the-loop review."""
from typing import Any, Dict, List, Literal, TypedDict
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger


class ApplicationState(TypedDict):
    """State for application review workflow."""
    # Input data
    user_id: str
    user_profile: Dict[str, Any]
    job: Dict[str, Any]
    matched_projects: List[Dict[str, Any]]
    
    # Generated content
    resume: Dict[str, Any]
    cover_letter: Dict[str, Any]
    
    # Review state
    status: str  # "pending_review", "approved", "rejected", "editing"
    review_feedback: Dict[str, Any]
    
    # Metadata
    application_id: str
    created_at: str
    reviewed_at: str


class HumanReviewWorkflow:
    """
    LangGraph workflow for human review of generated applications.
    
    Workflow:
    1. Generate documents (resume + cover letter)
    2. Wait for human review (INTERRUPT)
    3. Handle decision (approve/edit/reject)
    4. Send application (if approved)
    """
    
    def __init__(self, db_session=None):
        self.db = db_session
        self.checkpointer = MemorySaver()  # Persists state between interrupts
        self.graph = self._build_graph()
        logger.info("Human review workflow initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Create graph
        workflow = StateGraph(ApplicationState)
        
        # Add nodes
        workflow.add_node("generate_documents", self._generate_documents)
        workflow.add_node("wait_for_review", self._wait_for_review)
        workflow.add_node("process_approval", self._process_approval)
        workflow.add_node("process_edits", self._process_edits)
        workflow.add_node("process_rejection", self._process_rejection)
        
        # Define edges
        workflow.set_entry_point("generate_documents")
        workflow.add_edge("generate_documents", "wait_for_review")
        
        # Conditional routing after review
        workflow.add_conditional_edges(
            "wait_for_review",
            self._route_after_review,
            {
                "approved": "process_approval",
                "edit": "process_edits",
                "rejected": "process_rejection"
            }
        )
        
        # End states
        workflow.add_edge("process_approval", END)
        workflow.add_edge("process_edits", "generate_documents")  # Loop back
        workflow.add_edge("process_rejection", END)
        
        return workflow.compile(
            checkpointer=self.checkpointer,
            interrupt_before=["wait_for_review"]  # Pause here for human input
        )
    
    async def _generate_documents(self, state: ApplicationState) -> ApplicationState:
        """Generate resume and cover letter."""
        logger.info(f"Generating documents for job: {state['job'].get('title')}")
        
        # Import agents
        from app.agents.resume_generator import ResumeGeneratorAgent
        from app.agents.cover_letter_writer import CoverLetterWriterAgent
        
        # Generate resume
        resume_agent = ResumeGeneratorAgent()
        resume_result = await resume_agent.run({
            "user_profile": state["user_profile"],
            "job": state["job"],
            "matched_projects": state["matched_projects"]
        })
        
        # Generate cover letter
        cover_letter_agent = CoverLetterWriterAgent()
        cover_letter_result = await cover_letter_agent.run({
            "user_profile": state["user_profile"],
            "job": state["job"],
            "resume_data": resume_result.data.get("resume_data", {}),
            "matched_projects": state["matched_projects"]
        })
        
        # Update state
        state["resume"] = resume_result.data
        state["cover_letter"] = cover_letter_result.data
        state["status"] = "pending_review"
        
        logger.info("✅ Documents generated, waiting for review")
        
        return state
    
    async def _wait_for_review(self, state: ApplicationState) -> ApplicationState:
        """
        Wait for human review - this is where the workflow pauses.
        
        The workflow will interrupt here and wait for human input.
        """
        logger.info("⏸️  Workflow paused for human review")
        
        # This node doesn't modify state, just marks it as waiting
        state["status"] = "awaiting_review"
        
        return state
    
    def _route_after_review(self, state: ApplicationState) -> Literal["approved", "edit", "rejected"]:
        """
        Route based on review decision.
        
        This is called after human provides feedback.
        """
        feedback = state.get("review_feedback", {})
        decision = feedback.get("decision", "rejected")
        
        logger.info(f"Review decision: {decision}")
        
        if decision == "approved":
            return "approved"
        elif decision == "edit":
            return "edit"
        else:
            return "rejected"
    
    async def _process_approval(self, state: ApplicationState) -> ApplicationState:
        """Process approved application."""
        logger.info("✅ Application approved")
        
        state["status"] = "approved"
        state["reviewed_at"] = datetime.utcnow().isoformat()
        
        # TODO: Send application via email
        # await self._send_application(state)
        
        return state
    
    async def _process_edits(self, state: ApplicationState) -> ApplicationState:
        """Process edit request - will loop back to generation."""
        logger.info("✏️  Processing edits")
        
        feedback = state.get("review_feedback", {})
        edits = feedback.get("edits", {})
        
        # Apply edits to user profile or job context
        if "resume_edits" in edits:
            # Merge edits into user profile
            state["user_profile"].update(edits["resume_edits"])
        
        if "cover_letter_tone" in edits:
            # Update tone preference
            state["cover_letter_tone"] = edits["cover_letter_tone"]
        
        state["status"] = "regenerating"
        
        return state
    
    async def _process_rejection(self, state: ApplicationState) -> ApplicationState:
        """Process rejected application."""
        logger.info("❌ Application rejected")
        
        state["status"] = "rejected"
        state["reviewed_at"] = datetime.utcnow().isoformat()
        
        feedback = state.get("review_feedback", {})
        rejection_reason = feedback.get("reason", "No reason provided")
        
        logger.info(f"Rejection reason: {rejection_reason}")
        
        return state
    
    async def start_application_review(
        self,
        user_id: str,
        user_profile: Dict[str, Any],
        job: Dict[str, Any],
        matched_projects: List[Dict[str, Any]],
        application_id: str
    ) -> Dict[str, Any]:
        """
        Start a new application review workflow.
        
        Returns:
            Initial state with thread_id for resuming later
        """
        import uuid
        
        thread_id = f"review_{application_id}"
        
        initial_state = ApplicationState(
            user_id=user_id,
            user_profile=user_profile,
            job=job,
            matched_projects=matched_projects,
            resume={},
            cover_letter={},
            status="generating",
            review_feedback={},
            application_id=application_id,
            created_at=datetime.utcnow().isoformat(),
            reviewed_at=""
        )
        
        # Run workflow until interrupt
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # This will run until it hits the interrupt point
            result = await self.graph.ainvoke(initial_state, config)
            
            return {
                "thread_id": thread_id,
                "application_id": application_id,
                "status": result["status"],
                "resume": result["resume"],
                "cover_letter": result["cover_letter"],
                "message": "Documents generated. Please review and provide feedback."
            }
            
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            raise
    
    async def submit_review(
        self,
        thread_id: str,
        decision: Literal["approved", "edit", "rejected"],
        edits: Dict[str, Any] = None,
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Submit human review decision and resume workflow.
        
        Args:
            thread_id: Thread ID from start_application_review
            decision: "approved", "edit", or "rejected"
            edits: Optional edits to apply if decision is "edit"
            reason: Optional reason if rejected
        """
        logger.info(f"Submitting review for {thread_id}: {decision}")
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get current state
        current_state = await self.graph.aget_state(config)
        
        if not current_state:
            raise ValueError(f"No workflow found for thread_id: {thread_id}")
        
        # Update state with review feedback
        state = current_state.values
        state["review_feedback"] = {
            "decision": decision,
            "edits": edits or {},
            "reason": reason,
            "reviewed_at": datetime.utcnow().isoformat()
        }
        
        # Resume workflow from interrupt
        result = await self.graph.ainvoke(state, config)
        
        return {
            "thread_id": thread_id,
            "status": result["status"],
            "message": self._get_status_message(result["status"]),
            "final_state": result
        }
    
    def _get_status_message(self, status: str) -> str:
        """Get human-readable status message."""
        messages = {
            "approved": "✅ Application approved and ready to send",
            "rejected": "❌ Application rejected",
            "regenerating": "🔄 Regenerating documents with your edits",
            "pending_review": "⏸️  Waiting for your review"
        }
        return messages.get(status, f"Status: {status}")
    
    async def get_review_status(self, thread_id: str) -> Dict[str, Any]:
        """Get current status of a review workflow."""
        config = {"configurable": {"thread_id": thread_id}}
        
        state = await self.graph.aget_state(config)
        
        if not state:
            raise ValueError(f"No workflow found for thread_id: {thread_id}")
        
        return {
            "thread_id": thread_id,
            "status": state.values.get("status"),
            "application_id": state.values.get("application_id"),
            "job_title": state.values.get("job", {}).get("title"),
            "company": state.values.get("job", {}).get("company"),
            "created_at": state.values.get("created_at"),
            "reviewed_at": state.values.get("reviewed_at")
        }
