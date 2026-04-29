import streamlit as st
import uuid
import plotly.io as pio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.messages import HumanMessage, AIMessageChunk
from scout.graph import Agent
from scout.prompts import prompts
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Scout Chat", page_icon="🍽️", layout="wide")

st.title("🍽️ Scout - Delishes Data Analyst")
st.markdown("Ask Scout about creators, customers, revenue, or request visualizations!")


@st.cache_resource
def get_agent():
    return Agent(
        name="Scout",
        system_prompt=prompts.scout_system_prompt,
        model="gpt-4o-mini",
        temperature=0.1,
    )


agent = get_agent()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "current_chart" not in st.session_state:
    st.session_state.current_chart = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("thinking"):
            with st.expander("🔍 Thinking & Tool Calls", expanded=False):
                st.markdown(message["thinking"])
        st.markdown(message["content"])
        if "chart" in message:
            st.plotly_chart(message["chart"], use_container_width=True)

if prompt := st.chat_input("What would you like to know?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        thinking_container = st.status("🔍 Scout is thinking...", expanded=True)
        response_placeholder = st.empty()

        full_response = ""
        thinking_log = ""
        has_used_tools = False
        pending_content = ""
        last_node = ""
        tool_calls = {}

        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        stream = agent.runnable.stream(
            input={"messages": [HumanMessage(content=prompt)]},
            config=config,
            stream_mode="messages",
        )

        for message_chunk, metadata in stream:
            node = metadata.get("langgraph_node", "")

            # Detect node transitions to reset per-round state
            if node != last_node:
                if node == "chatbot" and last_node == "tools":
                    # New chatbot round after tools — any content buffered
                    # in the main area from a previous speculative display
                    # needs to be moved to thinking if tools were used
                    if pending_content:
                        thinking_log += f"**Planning:**\n{pending_content}\n\n"
                        with thinking_container:
                            st.markdown(f"**Planning:**\n{pending_content}")
                        pending_content = ""
                        full_response = ""
                        response_placeholder.empty()
                last_node = node

            if node == "tools":
                has_used_tools = True
                if hasattr(message_chunk, "content") and message_chunk.content:
                    output = message_chunk.content
                    preview = output[:500] + "..." if len(output) > 500 else output
                    thinking_log += f"**Tool Result:**\n{preview}\n\n"
                    with thinking_container:
                        st.markdown(f"**Tool Result:**\n{preview}")

            elif node == "chatbot" and isinstance(message_chunk, AIMessageChunk):
                # Handle tool call chunks — always go to thinking
                if message_chunk.tool_call_chunks:
                    has_used_tools = True

                    # Demote any content currently in the main response area
                    if pending_content:
                        thinking_log += f"**Planning:**\n{pending_content}\n\n"
                        with thinking_container:
                            st.markdown(f"**Planning:**\n{pending_content}")
                        pending_content = ""
                        full_response = ""
                        response_placeholder.empty()

                    for tool_chunk in message_chunk.tool_call_chunks:
                        tc_id = tool_chunk.get("id")
                        if tc_id and tc_id not in tool_calls:
                            tool_calls[tc_id] = {
                                "name": "",
                                "args": "",
                                "placeholder": None,
                            }

                        active_id = tc_id or (
                            list(tool_calls.keys())[-1] if tool_calls else None
                        )
                        if not active_id:
                            continue

                        if tool_chunk.get("name"):
                            tool_calls[active_id]["name"] = tool_chunk["name"]

                        args = tool_chunk.get("args", "")
                        if args:
                            tool_calls[active_id]["args"] += args

                        name = tool_calls[active_id]["name"]
                        if name:
                            with thinking_container:
                                if not tool_calls[active_id]["placeholder"]:
                                    st.write(f"🛠️ **Calling:** `{name}`")
                                    tool_calls[active_id]["placeholder"] = st.empty()
                                if tool_calls[active_id]["args"]:
                                    tool_calls[active_id]["placeholder"].code(
                                        tool_calls[active_id]["args"], language="json"
                                    )

                # Handle text content
                if message_chunk.content:
                    content = message_chunk.content
                    if isinstance(content, list):
                        text = "".join(
                            block.get("text", "") if isinstance(block, dict) else str(block)
                            for block in content
                        )
                    else:
                        text = content

                    if text:
                        pending_content += text
                        full_response += text
                        response_placeholder.markdown(full_response + "▌")

        # Finalize thinking log with any remaining tool call info
        for tc in tool_calls.values():
            if tc["name"]:
                thinking_log += f"**Tool Call:** `{tc['name']}`\n```json\n{tc['args']}\n```\n\n"

        if has_used_tools:
            thinking_container.update(
                label="🔍 Thinking & Tool Calls",
                state="complete",
                expanded=False,
            )
        else:
            thinking_container.update(
                label="⚡ Direct Response",
                state="complete",
                expanded=False,
            )

        response_placeholder.markdown(full_response)

        new_message = {
            "role": "assistant",
            "content": full_response,
            "thinking": thinking_log if has_used_tools else "",
        }

        thread_state = agent.runnable.get_state(config=config)
        if "chart_json" in thread_state.values:
            chart_json = thread_state.values["chart_json"]
            if chart_json and chart_json != st.session_state.current_chart:
                fig = pio.from_json(chart_json)
                st.plotly_chart(fig, use_container_width=True)
                new_message["chart"] = fig
                st.session_state.current_chart = chart_json

        st.session_state.messages.append(new_message)
