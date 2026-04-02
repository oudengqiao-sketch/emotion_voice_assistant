from rag.retriever import retrieve
from agent.prompt_builder import build_prompt



def run_agent(user_text, emotion, memory_manager, llm, decide_tool, call_tool):
    memory_context = memory_manager.get_context()
    tool_name = decide_tool(user_text)
    tool_result = call_tool(tool_name, user_text, emotion)
    rag_context = retrieve(user_text, memory_context.get("long_term_memory", ""))
    prompt = build_prompt(
        user_text=user_text,
        emotion=emotion,
        memory_context=memory_context,
        tool_result=tool_result,
        rag_context=rag_context,
    )

    llm_output = llm(
        prompt,
        max_tokens=20,
        temperature=0.5,
        stop=["\n", "用户输入：", "请开始回答："],
    )

    return {
        "tool_name": tool_name,
        "tool_result": tool_result,
        "memory_context": memory_context,
        "rag_context": rag_context,
        "prompt": prompt,
        "llm_output": llm_output["choices"][0]["text"].strip(),
    }
