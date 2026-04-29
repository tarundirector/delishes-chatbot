from pydantic import BaseModel
from typing import Annotated, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from scout.tools import query_db, generate_visualization
from scout.prompts import prompts


def update_chart(existing: str, new: str) -> str:
    """Simple reducer that always returns the newest chart JSON."""
    return new


class ScoutState(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages] = []
    chart_json: Annotated[str, update_chart] = ""


class Agent:
    """LangGraph-based conversational agent with tool-calling capabilities."""

    def __init__(
            self, 
            name: str, 
            tools: List = [query_db, generate_visualization],
            model: str = "gpt-4o-mini", 
            system_prompt: str = "You are a helpful assistant.",
            temperature: float = 0.1
            ):
        self.name = name
        self.tools = tools
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature
            ).bind_tools(self.tools)
        
        self.runnable = self.build_graph()


    def build_graph(self):
        """
        Build the LangGraph application.
        """
        def scout_node(state: ScoutState):
            response = self.llm.invoke(
                [SystemMessage(content=self.system_prompt)] +
                state.messages
                )
            return {"messages": [response]}
        
        def router(state: ScoutState) -> str:
            last_message = state.messages[-1]
            if not last_message.tool_calls:
                return END
            else:
                return "tools"

        builder = StateGraph(ScoutState)

        builder.add_node("chatbot", scout_node)
        builder.add_node("tools", ToolNode(self.tools))

        builder.add_edge(START, "chatbot")
        builder.add_conditional_edges("chatbot", router, ["tools", END])
        builder.add_edge("tools", "chatbot")

        return builder.compile(checkpointer=MemorySaver())
    

    def invoke(self, message: str, **kwargs) -> str:
        result = self.runnable.invoke(
            input={"messages": [HumanMessage(content=message)]},
            **kwargs,
        )
        return result["messages"][-1].content


agent = Agent(
        name="Scout",
        system_prompt=prompts.scout_system_prompt
        )
graph = agent.build_graph()
