"""Smolagents workers; LangGraph owns the transitions, not the LLM."""
import json
import re
from smolagents import ToolCallingAgent
from tools.agent_toolsets import PLANNER_TOOLS, CODER_TOOLS, TESTER_TOOLS
import ast


def parse_result(value):

    # Handle responses already returned as dictionaries
    if isinstance(value, dict):
        return value

    raw = str(value).strip()

    # Remove optional Markdown JSON formatting
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.S)
    candidate = match.group(1) if match else raw

    # First try strict JSON
    try:
        result = json.loads(candidate)

        if isinstance(result, dict):
            return result

    except (ValueError, TypeError):
        pass

    # Also support Python dictionary representations
    try:
        result = ast.literal_eval(candidate)

        if isinstance(result, dict):
            return result

    except (ValueError, SyntaxError, TypeError, RecursionError):
        pass

    # Escalate only when the response cannot be parsed
    return {
        "outcome": "escalate",
        "issue": "Agent returned unparseable output: " + raw[:1200]
    }

def validate_coder_answer(answer, memory, agent):

    result = parse_result(answer)

    # Reject responses that could not be parsed
    issue = str(result.get("issue", ""))

    if issue.startswith((
        "Agent returned unparseable output:",
        "Agent returned non-JSON output:"
    )):
        return False

    # Require a recognised outcome
    if result.get("outcome") not in ("ok", "escalate"):
        return False

    # Successful results must include an implementation summary
    # and a list of files
    if result["outcome"] == "ok":
        return (
            isinstance(result.get("summary"), str)
            and isinstance(result.get("files"), list)
        )

    # Escalations must explain the blocker
    return bool(issue.strip())


def make_agent(model, role, tools, instructions):
    return ToolCallingAgent(name=role, description=role + " worker", model=model,
                            tools=tools, instructions=instructions, max_steps=12)


def create_workers(model):
    planner = make_agent(model, "planner", PLANNER_TOOLS, """You are the technical planner. Read existing files when needed. Never write code or files. Break requirements into components, file responsibilities, APIs, design heuristics, acceptance criteria, test cases, and a Mermaid UML-style class/component diagram when appropriate. Avoid overengineering. Prefer Python standard library, but basic HTML/CSS/JS websites are supported. Do not assume other engines or compilers exist. Respond ONLY with a JSON object: {"outcome":"ok|escalate","plan":"detailed plan","requirements":["testable requirement"],"issue":"reason if blocked"}. Escalate if requirements are ambiguous or capabilities uncertain.""")
    coder = make_agent(model, "coder", CODER_TOOLS, """Implement the planner's plan inside the workspace using tools. You may create Python, HTML, CSS, JS and supporting text files. Do not claim a file was written unless the tool confirms it. Do not change tests. If blocked or if the plan conflicts with requirements, escalate; do not silently choose. Respond ONLY as JSON: {"outcome":"ok|escalate","summary":"what was implemented","files":["relative paths"],"issue":"blocker if any"}.""")
    coder.final_answer_checks.append(validate_coder_answer)
    tester = make_agent(model, "tester", TESTER_TOOLS, """Independently verify the product against the original requirements, not merely the coder's claims. Inspect source, create Python tests with write_test_file and execute via Docker execute_file. HTML/CSS/JS may be checked statically but never claim browser validation without a browser. Do not edit implementation. If tests fail, describe exact evidence; distinguish bugs, missing requirements, unsupported tooling and disagreements. Respond ONLY as JSON: {"outcome":"pass|fail|escalate","report":"tests performed, actual results and limitations","issue":"specific failure or disagreement"}.""")
    supervisor = make_agent(model, "supervisor", [], """You are ONLY an intermediary for escalations and the final independent reviewer. Do not implement, plan, run tests or call workers. Review state evidence and choose the responsible next node. Prefer returning a failed test to coder; if requirements or design are defective send to planner; if testing evidence is incomplete send to tester. Request human clarification if essential information is missing; stop if tooling cannot support task. Do not approve without test evidence. If tester says pass but evidence is incomplete, send to tester. Reply ONLY JSON: {"decision":"planner|coder|tester|approve|clarify|stop","reason":"specific explanation"}. Decisions must be grounded in the provided context.""")
    return planner, coder, tester, supervisor


def create_nodes(model):
    planner, coder, tester, supervisor = create_workers(model)

    def planner_node(s):
        response = parse_result(planner.run("Original user request:\n" + s['user_task'] + "\nPrevious issue/decision: " + s['issue'] + " / " + s['decision']))
        if response.get('outcome') != 'ok' or not response.get('plan'):
            return {'issue': response.get('issue', 'Planner did not produce a plan'), 'issue_source':'planner', 'status':'escalated', 'history':s['history'] + ['planner: escalated']}
        return {'plan':str(response['plan']), 'requirements':response.get('requirements', []), 'issue':'', 'issue_source':'', 'status':'planned', 'test_status':'not_run', 'test_report':'', 'history':s['history'] + ['planner: planned']}

    def coder_node(s):
        attempt = s['iteration'] + 1
        response = parse_result(coder.run(f"USER REQUEST:\n{s['user_task']}\nREQUIREMENTS: {s['requirements']}\nPLAN:\n{s['plan']}\nPREVIOUS TEST REPORT:\n{s['test_report']}\nSUPERVISOR DECISION: {s['decision']}\nIMPLEMENTATION ATTEMPT: {attempt}"))
        base = {'iteration':attempt, 'history':s['history'] + [f'coder: attempt {attempt}']}
        if response.get('outcome') != 'ok':
            return {**base, 'status':'escalated', 'issue_source':'coder', 'issue':response.get('issue', 'Coder blocked')}
        return {**base, 'implementation':str(response.get('summary','')) + '\nFiles: ' + str(response.get('files',[])), 'status':'coded', 'test_status':'not_run', 'issue':'', 'issue_source':''}

    def tester_node(s):
        response = parse_result(tester.run(f"USER REQUEST:\n{s['user_task']}\nREQUIREMENTS: {s['requirements']}\nPLAN:\n{s['plan']}\nIMPLEMENTATION:\n{s['implementation']}\nTest independently and report actual evidence."))
        outcome = response.get('outcome', 'escalate')
        if outcome not in ('pass','fail','escalate'):
            outcome = 'escalate'
        return {'test_status':outcome, 'test_report':str(response.get('report','')), 'issue':str(response.get('issue','')) if outcome != 'pass' else '', 'issue_source':'tester' if outcome != 'pass' else '', 'status':'tested' if outcome == 'pass' else 'escalated', 'history':s['history'] + [f'tester: {outcome}']}

    def supervisor_node(s):
        response = parse_result(supervisor.run(f"ORIGINAL REQUEST: {s['user_task']}\nREQUIREMENTS: {s['requirements']}\nPLAN: {s['plan']}\nIMPLEMENTATION: {s['implementation']}\nTEST STATUS: {s['test_status']}\nTEST REPORT: {s['test_report']}\nESCALATION SOURCE: {s['issue_source']}\nISSUE: {s['issue']}\nITERATION: {s['iteration']}/{s['max_iterations']}\nHISTORY: {s['history']}\nDecide the next step. If this is a final review and tests passed, approve only if requirements have adequate evidence."))
        decision = response.get('decision','stop')
        if decision not in ('planner','coder','tester','approve','clarify','stop'):
            decision = 'stop'
        visits = s['supervisor_visits'] + 1
        if decision == 'approve' and s['test_status'] != 'pass':
            decision = 'stop'
        if decision == 'coder' and s['iteration'] >= s['max_iterations']:
            decision = 'stop'
        if visits >= s['max_iterations'] * 3 + 3 and decision not in ('approve','clarify','stop'):
            decision = 'stop'
        return {'next_node':decision, 'decision':str(response.get('reason','')), 'final_review':str(response.get('reason','')), 'supervisor_visits':visits, 'status': 'success' if decision == 'approve' else ('needs_clarification' if decision == 'clarify' else ('failed' if decision == 'stop' else 'redirected')), 'history':s['history'] + [f'supervisor: {decision}']}
    return planner_node, coder_node, tester_node, supervisor_node
