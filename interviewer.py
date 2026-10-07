from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from retriever import getcontext
import logging
logging.getLogger("google_genai").setLevel(logging.ERROR)

load_dotenv()  # reads GOOGLE_API_KEY from .env

def to_text(content):
    if isinstance(content, str):
        return content
    return "".join(b["text"] for b in content if b.get("type") == "text")

# Check Google AI Studio for a current Gemini Flash model name; names change often
MODEL_NAME = "gemini-3.1-flash-lite"
llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0.4)

QUESTION_PROMPT = """You are a technical interviewer. A student is presenting their project.
Use ONLY the project text below. Do not invent features, files or tools that are not in it.
If the text is not enough to ask a good question, say "NOT ENOUGH INFO".

Project text:
{context}

Ask ONE specific interview question about a design decision, trade-off or
possible failure in this project. Do not ask for a simple definition.
Return only the question."""

EVAL_PROMPT = """You are a technical interviewer.
Only praise what the student actually said. If the student says they don't know, say so plainly and teach the answer from the project text
Never claim the student said something they did not say.
Project text:
{context}

Question you asked: {question}
Student's answer: {answer}

Compare the answer with the project text. In 3-4 lines, say:
1. What was correct
2. What was wrong or missing (only if the project text shows it)
3. One follow-up question"""

def ask_question(topic,project_id):
    context = getcontext(topic,project_id, k=3)
    reply = llm.invoke(QUESTION_PROMPT.format(context=context))
    return to_text(reply.content), context

def evaluate_answer(question, answer, context):
    reply = llm.invoke(EVAL_PROMPT.format(context=context, question=question, answer=answer))
    return to_text(reply.content)

if __name__ == "__main__":
    question, context = ask_question("what problem, the project is solving?")
    print("Q:", question)
    answer = input("Your answer: ")
    print(evaluate_answer(question, answer, context))