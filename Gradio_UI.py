# gradio_UI.py

import os
import re
import mimetypes
import shutil
from typing import Optional

import gradio as gr

from smolagents.agent_types import AgentText, AgentImage, AgentAudio, handle_agent_output_types
from smolagents.agents import ActionStep, MultiStepAgent
from smolagents.memory import MemoryStep
from smolagents.utils import _is_package_available

def pull_messages_from_step(step_log: MemoryStep):
    if isinstance(step_log, ActionStep):
        step_number = f"Step {step_log.step_number}" if step_log.step_number is not None else ""
        yield gr.ChatMessage(role="assistant", content=f"**{step_number}**")

        if hasattr(step_log, "model_output") and step_log.model_output is not None:
            model_output = re.sub(r"```.?\s*<end_code>", "```", step_log.model_output.strip())
            yield gr.ChatMessage(role="assistant", content=model_output)

        if hasattr(step_log, "tool_calls") and step_log.tool_calls:
            tool_call = step_log.tool_calls[0]
            content = str(tool_call.arguments.get("answer", tool_call.arguments)) if isinstance(tool_call.arguments, dict) else str(tool_call.arguments)
            if tool_call.name == "python_interpreter":
                content = f"```python\n{re.sub(r'<end_code>', '', content).strip()}\n```"
            tool_msg = gr.ChatMessage(
                role="assistant",
                content=content,
                metadata={"title": f"🛠️ Used tool {tool_call.name}", "id": "tool_call", "status": "pending"},
            )
            yield tool_msg
            if step_log.observations:
                yield gr.ChatMessage(role="assistant", content=step_log.observations.strip(), metadata={"title": "📝 Execution Logs", "parent_id": "tool_call", "status": "done"})
            if step_log.error:
                yield gr.ChatMessage(role="assistant", content=str(step_log.error), metadata={"title": "💥 Error", "parent_id": "tool_call", "status": "done"})
            tool_msg.metadata["status"] = "done"

        elif step_log.error:
            yield gr.ChatMessage(role="assistant", content=str(step_log.error), metadata={"title": "💥 Error"})

        meta = f"<span style='color:#bbb;font-size:12px;'>Input tokens: {getattr(step_log, 'input_token_count', 0)} | Output tokens: {getattr(step_log, 'output_token_count', 0)} | Duration: {round(getattr(step_log, 'duration', 0), 2)}</span>"
        yield gr.ChatMessage(role="assistant", content=meta)
        yield gr.ChatMessage(role="assistant", content="-----")

def stream_to_gradio(agent, task: str, reset_agent_memory: bool = False, additional_args: Optional[dict] = None):
    total_input_tokens = 0
    total_output_tokens = 0
    for step_log in agent.run(task, stream=True, reset=reset_agent_memory, additional_args=additional_args):
        if hasattr(agent.model, "last_input_token_count"):
            total_input_tokens += agent.model.last_input_token_count
            total_output_tokens += agent.model.last_output_token_count
            if isinstance(step_log, ActionStep):
                step_log.input_token_count = agent.model.last_input_token_count
                step_log.output_token_count = agent.model.last_output_token_count
        for message in pull_messages_from_step(step_log):
            yield message
    final_answer = handle_agent_output_types(step_log)
    if isinstance(final_answer, AgentText):
        yield gr.ChatMessage(role="assistant", content=f"**Final answer:**\n{final_answer.to_string()}")
    elif isinstance(final_answer, AgentImage):
        yield gr.ChatMessage(role="assistant", content={"path": final_answer.to_string(), "mime_type": "image/png"})
    elif isinstance(final_answer, AgentAudio):
        yield gr.ChatMessage(role="assistant", content={"path": final_answer.to_string(), "mime_type": "audio/wav"})
    else:
        yield gr.ChatMessage(role="assistant", content=f"**Final answer:** {str(final_answer)}")

class GradioUI:
    def __init__(self, agent: MultiStepAgent):
        if not _is_package_available("gradio"):
            raise ModuleNotFoundError("Please install 'gradio' with: pip install 'smolagents[gradio]'")
        self.agent = agent

    def interact_with_agent(self, prompt, messages):
        messages.append(gr.ChatMessage(role="user", content=prompt))
        yield messages
        for msg in stream_to_gradio(self.agent, task=prompt):
            messages.append(msg)
            yield messages
        yield messages

    # def launch(self):
    #     with gr.Blocks(fill_height=True) as demo:
    #         stored_messages = gr.State([])
    #         chatbot = gr.Chatbot(label="🌍 Mood-Based Travel Agent", type="messages")
    #         user_input = gr.Textbox(lines=1, label="Describe your mood")
    #         user_input.submit(
    #             lambda text, hist: (hist + [gr.ChatMessage(role="user", content=text)], ""),
    #             [user_input, stored_messages],
    #             [stored_messages, user_input],
    #         ).then(self.interact_with_agent, [user_input, stored_messages], [chatbot])
    #     demo.launch(debug=True, share=True)

    def launch(self):
        def run_agent_interface(prompt):
            messages = []
            for msg in stream_to_gradio(self.agent, task=prompt):
                messages.append(msg)
            return "\n".join([m.content if isinstance(m.content, str) else str(m.content) for m in messages])


        demo = gr.Interface(
            fn=run_agent_interface,
            inputs=gr.Textbox(
                label="Describe your mood",
                placeholder="e.g., I need a lemon-scented reset by the sea...",
                lines=1
            ),
            outputs=gr.Textbox(label="Response"),
            title="Mood-Based Travel Agent",
            description="Plan your perfect Mediterranean escape, one mood at a time.",
            theme="default",
            api_name="predict"
        )

        demo.launch(debug=True, share=True)

__all__ = ["GradioUI", "stream_to_gradio"]