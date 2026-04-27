import json
import html
from IPython.display import display, HTML


def _safe_json(obj):
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)


def _role(msg):
    t = msg.__class__.__name__
    return t.replace("Message", "")


def display_langchain_messages_dark(messages, show_full_metadata=False):
    role_colors = {
        "Human": "#60a5fa",   # blue
        "AI": "#34d399",      # green
        "Tool": "#c084fc",    # purple
        "System": "#fb923c",  # orange
    }

    cards = []

    for msg in messages:
        role = _role(msg)
        color = role_colors.get(role, "#e5e7eb")

        content = getattr(msg, "content", "")
        if isinstance(content, str):
            content_html = html.escape(content)
        else:
            content_html = html.escape(_safe_json(content))

        tool_calls = getattr(msg, "tool_calls", None)
        invalid_tool_calls = getattr(msg, "invalid_tool_calls", None)
        usage = getattr(msg, "usage_metadata", None)
        response_metadata = getattr(msg, "response_metadata", None)
        additional_kwargs = getattr(msg, "additional_kwargs", None)

        tool_html = ""
        if tool_calls:
            tool_html = f"""
            <details style="margin-top:12px;">
                <summary style="
                    cursor:pointer;
                    color:#93c5fd;
                    font-weight:700;
                    outline:none;
                ">🔧 Tool Calls</summary>
                <pre style="
                    margin-top:10px;
                    padding:12px;
                    background:#020617;
                    border:1px solid #334155;
                    border-radius:10px;
                    color:#e2e8f0;
                    white-space:pre-wrap;
                    overflow-x:auto;
                ">{html.escape(_safe_json(tool_calls))}</pre>
            </details>
            """

        invalid_tool_html = ""
        if invalid_tool_calls:
            invalid_tool_html = f"""
            <details style="margin-top:12px;">
                <summary style="
                    cursor:pointer;
                    color:#fda4af;
                    font-weight:700;
                    outline:none;
                ">⚠️ Invalid Tool Calls</summary>
                <pre style="
                    margin-top:10px;
                    padding:12px;
                    background:#020617;
                    border:1px solid #334155;
                    border-radius:10px;
                    color:#fecdd3;
                    white-space:pre-wrap;
                    overflow-x:auto;
                ">{html.escape(_safe_json(invalid_tool_calls))}</pre>
            </details>
            """

        meta_html = ""
        if show_full_metadata:
            meta_payload = {
                "usage_metadata": usage,
                "response_metadata": response_metadata,
                "additional_kwargs": additional_kwargs,
            }
            meta_html = f"""
            <details style="margin-top:12px;">
                <summary style="
                    cursor:pointer;
                    color:#fca5a5;
                    font-weight:700;
                    outline:none;
                ">📊 Metadata</summary>
                <pre style="
                    margin-top:10px;
                    padding:12px;
                    background:#020617;
                    border:1px solid #334155;
                    border-radius:10px;
                    color:#e2e8f0;
                    white-space:pre-wrap;
                    overflow-x:auto;
                ">{html.escape(_safe_json(meta_payload))}</pre>
            </details>
            """

        tool_name = getattr(msg, "name", None)
        tool_id = getattr(msg, "tool_call_id", None)

        tool_info_parts = []
        if tool_name:
            tool_info_parts.append(
                f"<span><b style='color:#f8fafc;'>Tool:</b> <span style='color:#e2e8f0;'>{html.escape(str(tool_name))}</span></span>"
            )
        if tool_id:
            tool_info_parts.append(
                f"<span><b style='color:#f8fafc;'>Call ID:</b> <span style='color:#fde68a;'>{html.escape(str(tool_id))}</span></span>"
            )

        tool_info = ""
        if tool_info_parts:
            tool_info = f"""
            <div style="
                margin-top:10px;
                color:#d1d5db;
                font-size:13px;
                display:flex;
                gap:18px;
                flex-wrap:wrap;
            ">
                {' '.join(tool_info_parts)}
            </div>
            """

        card = f"""
        <div style="
            background:#0f172a;
            border:1px solid #1e293b;
            border-left:6px solid {color};
            border-radius:14px;
            padding:16px 18px;
            margin:14px 0;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            color:#e5e7eb;
            box-shadow: 0 1px 3px rgba(0,0,0,0.35);
        ">
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:flex-start;
                gap:16px;
                margin-bottom:12px;
            ">
                <div>
                    <span style="
                        color:{color};
                        font-weight:800;
                        font-size:15px;
                    ">
                        {html.escape(role)}
                    </span>

                    <span style="
                        color:#facc15;
                        margin-left:10px;
                        font-weight:700;
                        font-size:13px;
                    ">
                        {html.escape(msg.__class__.__name__)}
                    </span>
                </div>

                <div style="
                    color:#fde68a;
                    font-size:12px;
                    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                    word-break:break-all;
                    text-align:right;
                ">
                    {html.escape(str(getattr(msg, "id", "")))}
                </div>
            </div>

            <div style="
                margin-top:2px;
            ">
                <div style="
                    color:#cbd5e1;
                    font-size:12px;
                    font-weight:700;
                    margin-bottom:8px;
                    letter-spacing:0.02em;
                    text-transform:uppercase;
                ">Content</div>

                <pre style="
                    white-space:pre-wrap;
                    margin:0;
                    padding:12px;
                    background:#020617;
                    border:1px solid #334155;
                    border-radius:10px;
                    color:#f8fafc;
                    overflow-x:auto;
                    line-height:1.5;
                ">{content_html}</pre>
            </div>

            {tool_info}
            {tool_html}
            {invalid_tool_html}
            {meta_html}
        </div>
        """
        cards.append(card)

    wrapper = f"""
    <div style="background:transparent; padding:4px 0;">
        {''.join(cards)}
    </div>
    """

    display(HTML(wrapper))
