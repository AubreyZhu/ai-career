# -*- coding: utf-8 -*-
import sys
import io
import streamlit as st
from openai import OpenAI
import json
import re
import datetime

# ================= 配置区域 =================
# 【重要修改】这里不再硬编码 Key，留给用户填写
DEFAULT_BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"

# ================= 页面设置 =================
st.set_page_config(page_title="AI 职业战略顾问 Pro (自带 Key 版)", layout="wide")
st.title("🚀 AI 职业战略顾问 Pro")
st.markdown("全流程深度分析：从人岗匹配到行业前瞻，再到实战演练。")
st.info("💡 **使用说明**：请在左侧边栏填入您自己的 DeepSeek API Key 即可开始使用。本工具不保存您的 Key。")

# ================= 辅助函数 =================

def get_score_style(score):
    if score >= 90: return "#006400", "🟢" 
    elif score >= 80: return "#32CD32", "🟩" 
    elif score >= 60: return "#FFD700", "🟨" 
    elif score >= 40: return "#FFA500", "🟧" 
    else: return "#DC143C", "🔴" 

def render_score_metric(label, score):
    hex_color, emoji = get_score_style(score)
    html = f"""
    <div style='background-color:{hex_color}; color:white; padding:15px; border-radius:8px; text-align:center; font-size:24px; font-weight:bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        {emoji} {score} / 100
    </div>
    <div style='text-align:center; margin-top:5px; color:#555; font-size:14px;'>{label}</div>
    """
    st.markdown(html, unsafe_allow_html=True)

def call_deepseek(messages, api_key, base_url, system_prompt="你是一位资深的职业战略顾问，擅长深度分析和详细指导。"):
    # 【重要修改】每次调用都使用用户传入的 Key
    if not api_key:
        return None
    
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        response = client.chat.completions.create(
            model=MODEL,
            messages=full_messages,
            temperature=0.7,
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        # 捕获具体的 API 错误（如 Key 无效）
        error_msg = str(e)
        if "invalid_api_key" in error_msg.lower():
            st.error("❌ API Key 无效！请检查左侧边栏输入的 Key 是否正确。")
        elif "quota" in error_msg.lower() or "balance" in error_msg.lower():
            st.error("💸 余额不足！您的 API Key 额度已用完，请充值。")
        else:
            st.error(f"AI 服务出错：{error_msg}")
        return None

def safe_json_loads(text):
    if not text: return None
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        text = text[start:end+1]
    try:
        return json.loads(text)
    except:
        return None

def nav_buttons(prev_step, next_step, action_func=None):
    cols = st.columns([1, 4, 1])
    with cols[0]:
        if prev_step is not None:
            if st.button("⬅️ 上一步", use_container_width=True):
                st.session_state.step = prev_step
                st.rerun()
        else:
            st.write("")
    with cols[2]:
        if next_step is not None:
            if st.button("下一步 ➡️", type="primary", use_container_width=True):
                if action_func: action_func()
                st.session_state.step = next_step
                st.rerun()
        else:
            st.write("")

def generate_doc_content(html_content, title):
    doc_header = f"""
    <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
    <head><meta charset='utf-8'><title>{title}</title></head><body>
    """
    doc_footer = "</body></html>"
    content = html_content.replace('\n', '<br>')
    content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
    content = re.sub(r'### (.*?)<br>', r'<h3>\1</h3>', content)
    content = re.sub(r'## (.*?)<br>', r'<h2>\1</h2>', content)
    content = re.sub(r'# (.*?)<br>', r'<h1>\1</h1>', content)
    return doc_header + content + doc_footer

# ================= 状态管理 =================
if 'step' not in st.session_state: st.session_state.step = 1

# 【持久化变量 - 用户输入】
if 'persist_mbti' not in st.session_state: st.session_state.persist_mbti = ""
if 'persist_dislikes' not in st.session_state: st.session_state.persist_dislikes = ""
if 'persist_location' not in st.session_state: st.session_state.persist_location = ""
if 'persist_resume' not in st.session_state: st.session_state.persist_resume = ""
if 'persist_jd' not in st.session_state: st.session_state.persist_jd = ""

# 【分析结果缓存】
if 'skill_analysis' not in st.session_state: st.session_state.skill_analysis = None
if 'personality_analysis' not in st.session_state: st.session_state.personality_analysis = None
if 'industry_report' not in st.session_state: st.session_state.industry_report = None
if 'upskilling_plan' not in st.session_state: st.session_state.upskilling_plan = None
if 'upskilling_raw_text' not in st.session_state: st.session_state.upskilling_raw_text = ""
if 'final_resume' not in st.session_state: st.session_state.final_resume = ""

# 面试相关
if 'interview_questions' not in st.session_state: st.session_state.interview_questions = None
if 'interview_feedback' not in st.session_state: st.session_state.interview_feedback = {}
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}

# ================= 侧边栏导航 (含 Key 设置) =================
with st.sidebar:
    st.header("🔑 设置与导航")
    
    # 【新增】API Key 输入框
    st.markdown("### 1. API Key 配置")
    user_api_key = st.text_input(
        "DeepSeek API Key", 
        type="password", 
        placeholder="sk-...", 
        help="请输入您自己的 DeepSeek API Key。Key 仅保存在当前浏览器会话中，刷新页面后需重新输入（或自行开启浏览器记住密码）。",
        key="api_key_input"
    )
    
    # 保存 Key 到 Session State
    if user_api_key:
        st.session_state.user_api_key = user_api_key
    elif 'user_api_key' not in st.session_state:
        st.session_state.user_api_key = ""
        
    # 检查 Key 是否有效（简单提示）
    if not st.session_state.user_api_key:
        st.warning("⚠️ **请先输入 API Key 才能开始分析！**")
    else:
        st.success("✅ Key 已就绪")

    st.divider()
    
    st.markdown("### 2. 全程导航")
    st.markdown("""
    <div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; font-size: 13px; color: #333;'>
    💡 <b>提示：</b><br>
    1. 点击此处可<b>随时跳转</b>查看已生成的报告。<br>
    2. 除非修改输入并点击<b>“开始深度分析”</b>，否则结果<b>不会丢失</b>。
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    step1_btn = st.button("1. 📝 基础信息", use_container_width=True, type="primary" if st.session_state.step == 1 else "secondary")
    step2_btn = st.button("2. 🎯 匹配度分析", use_container_width=True, type="primary" if st.session_state.step == 2 else "secondary")
    step3_btn = st.button("3. 📈 行业与计划", use_container_width=True, type="primary" if st.session_state.step == 3 else "secondary")
    step4_btn = st.button("4. 📄 战略简历", use_container_width=True, type="primary" if st.session_state.step == 4 else "secondary")
    step5_btn = st.button("5. 🎤 模拟面试", use_container_width=True, type="primary" if st.session_state.step == 5 else "secondary")
    
    st.divider()
    if st.button("🔄 完全重置 (清空所有)", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.step = 1
        st.rerun()

    # 跳转逻辑
    if step1_btn and st.session_state.step != 1:
        st.session_state.step = 1
        st.rerun()
    elif step2_btn and st.session_state.step != 2:
        st.session_state.step = 2
        st.rerun()
    elif step3_btn and st.session_state.step != 3:
        st.session_state.step = 3
        st.rerun()
    elif step4_btn and st.session_state.step != 4:
        st.session_state.step = 4
        st.rerun()
    elif step5_btn and st.session_state.step != 5:
        st.session_state.step = 5
        st.rerun()

# ================= 全局前置检查 =================
# 在任何步骤执行前，检查是否有 Key
if not st.session_state.get('user_api_key'):
    if st.session_state.step != 1:
        # 如果用户在中间步骤，但 Key 没了（比如刷新了），强制跳回第一步提示
        st.session_state.step = 1
        st.rerun()
    # 在第一步显示大提示
    st.error("👈 请在左侧边栏输入您的 **DeepSeek API Key** 以继续使用。")
    st.stop() # 停止后续代码执行

current_api_key = st.session_state.user_api_key

# ================= Step 1: 全量信息输入 =================
if st.session_state.step == 1:
    st.subheader("1. 📝 基础信息与深度画像")
    st.markdown("请尽可能详细地填写以下信息。*灰色框内为历史保存值，可修改*")
    st.info("💡 **重要**：修改以下内容后，必须点击底部的“开始深度分析”才会更新报告。仅切换页面不会丢失数据。")
    
    with st.form("main_input_form"):
        c1, c2 = st.columns(2)
        with c1:
            jd_input = st.text_area("岗位描述 (JD)", height=200, placeholder="粘贴完整的 Job Description...", value=st.session_state.get('persist_jd', ''))
        with c2:
            resume_input = st.text_area("你的简历内容", height=200, placeholder="粘贴你的简历全文...", value=st.session_state.get('persist_resume', ''))
        
        st.markdown("**👤 个人特质与偏好 (自动保存)**")
        c3, c4 = st.columns(2)
        with c3:
            mbti_input = st.text_input("MBTI 性格类型", value=st.session_state.persist_mbti, placeholder="例如：INTJ")
            location_input = st.text_input("地点/工时硬性要求", value=st.session_state.persist_location, placeholder="例如：必须北京")
        with c4:
            dislikes_input = st.text_area("最讨厌的工作内容/环境", value=st.session_state.persist_dislikes, placeholder="例如：讨厌无效会议", height=88)
        
        submitted = st.form_submit_button("🚀 开始深度分析 (重置旧报告)", type="primary", use_container_width=True)
        
        if submitted:
            if not jd_input or not resume_input:
                st.error("岗位描述和简历是必填项！")
            else:
                # 更新持久化数据
                st.session_state.persist_jd = jd_input
                st.session_state.persist_resume = resume_input
                st.session_state.persist_mbti = mbti_input
                st.session_state.persist_dislikes = dislikes_input
                st.session_state.persist_location = location_input
                
                # 清空分析结果
                st.session_state.skill_analysis = None
                st.session_state.personality_analysis = None
                st.session_state.industry_report = None
                st.session_state.upskilling_plan = None
                st.session_state.upskilling_raw_text = ""
                st.session_state.final_resume = ""
                st.session_state.interview_questions = None
                st.session_state.interview_feedback = {}
                st.session_state.user_answers = {}
                
                st.session_state.step = 2
                st.rerun()
    
    if st.session_state.skill_analysis:
        st.divider()
        st.success("✅ 已有分析报告生成！您可以直接点击左侧导航栏查看，或修改上方信息后重新分析。")
        if st.button("➡️ 直接前往匹配度分析", type="secondary", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

# ================= Step 2: 核心匹配度分析 =================
elif st.session_state.step == 2:
    st.subheader("2. 🎯 核心匹配度深度研判")
    
    if st.session_state.skill_analysis is None or st.session_state.personality_analysis is None:
        with st.spinner("AI 正在双线程分析硬技能与性格匹配度..."):
            
            prompt_skill = f"""
            分析硬技能匹配度。请详细列出优势和差距，不要省略细节。
            JD: {st.session_state.persist_jd}
            简历: {st.session_state.persist_resume}
            返回 JSON: {{'score': int, 'strengths': ['str'], 'gaps': ['gap'], 'summary': 'str'}}
            """
            
            prompt_pers = f"""
            分析性格与意愿匹配度。请深入分析性格是否适合该岗位核心职能。
            JD: {st.session_state.persist_jd}
            用户画像: MBTI={st.session_state.persist_mbti}, 讨厌={st.session_state.persist_dislikes}, 要求={st.session_state.persist_location}
            返回 JSON: {{'score': int, 'personality_fit': 'str', 'risk_alerts': ['alert'], 'advice': 'str'}}
            """
            
            # 【修改】传入 current_api_key 和 DEFAULT_BASE_URL
            res_skill_txt = call_deepseek([{"role": "user", "content": prompt_skill}], current_api_key, DEFAULT_BASE_URL)
            res_pers_txt = call_deepseek([{"role": "user", "content": prompt_pers}], current_api_key, DEFAULT_BASE_URL)
            
            # 如果 API 调用失败（返回 None），则停止生成，让用户检查 Key
            if res_skill_txt is None or res_pers_txt is None:
                st.stop()
            
            skill_data = safe_json_loads(res_skill_txt)
            pers_data = safe_json_loads(res_pers_txt)
            
            if skill_data: st.session_state.skill_analysis = skill_data
            else: st.session_state.skill_analysis = {"score": 50, "strengths": [], "gaps": [], "summary": "解析失败，请稍后重试"}
            
            if pers_data: st.session_state.personality_analysis = pers_data
            else: st.session_state.personality_analysis = {"score": 50, "personality_fit": "", "risk_alerts": [], "advice": ""}
            
            st.rerun()
    
    else:
        skill = st.session_state.skill_analysis
        pers = st.session_state.personality_analysis
        
        c1, c2 = st.columns(2)
        with c1:
            render_score_metric("硬技能匹配分", skill.get('score', 0))
            with st.expander("查看优势与差距", expanded=True):
                st.success("**✅ 核心优势:**\n" + "\n".join([f"- {s}" for s in skill.get('strengths', [])]))
                st.error("**⚠️ 技能差距:**\n" + "\n".join([f"- {g}" for g in skill.get('gaps', [])]))
                st.info(skill.get('summary', ''))
        
        with c2:
            render_score_metric("性格/意愿匹配分", pers.get('score', 0))
            with st.expander("查看性格分析与风险", expanded=True):
                st.markdown(f"**🧩 性格契合:** {pers.get('personality_fit', '')}")
                if pers.get('risk_alerts'):
                    st.warning("**🚩 潜在风险:**\n" + "\n".join([f"- {r}" for r in pers['risk_alerts']]))
                st.info(f"💡 **顾问建议:** {pers.get('advice', '')}")
        
        st.divider()
        nav_buttons(1, 3)

# ================= Step 3: 行业前景 + 技能补全 =================
elif st.session_state.step == 3:
    st.subheader("3. 📈 行业战略与技能提升计划")
    
    if st.session_state.industry_report is None or st.session_state.upskilling_plan is None:
        with st.spinner("AI 正在研判行业趋势并制定详细学习计划..."):
            
            prompt_ind = f"""
            详细分析行业前景、AI 替代风险及类似岗位。内容要丰富。
            JD: {st.session_state.persist_jd}
            返回 JSON: {{'industry_trend': 'str', 'industry_score': int, 'ai_risk_level': '高/中/低', 'ai_risk_detail': 'str', 'similar_roles': [{{'title':'', 'reason':''}}], 'strategic_advice': 'str'}}
            """
            
            gaps = st.session_state.skill_analysis.get('gaps', [])
            prompt_up = f"""
            针对技能差距制定非常详细的学习计划。
            差距列表: {gaps}
            目标岗位: {st.session_state.persist_jd[:200]}
            要求：为每个差距提供：1.学习路径 (3 步) 2.搜索关键词 3.微型实战项目 4.预计耗时。
            返回 JSON: {{'plan': [{{'gap': '', 'path': [], 'keywords': '', 'project': '', 'hours': ''}}]}}
            如果无法生成 JSON，请直接返回详细的文本计划。
            """
            
            ind_txt = call_deepseek([{"role": "user", "content": prompt_ind}], current_api_key, DEFAULT_BASE_URL)
            up_txt = call_deepseek([{"role": "user", "content": prompt_up}], current_api_key, DEFAULT_BASE_URL)
            
            if ind_txt is None or up_txt is None:
                st.stop()

            st.session_state.industry_report = safe_json_loads(ind_txt) if ind_txt else {}
            
            up_data = safe_json_loads(up_txt)
            if up_data and 'plan' in up_data:
                st.session_state.upskilling_plan = up_data.get('plan', [])
                st.session_state.upskilling_raw_text = ""
            else:
                st.session_state.upskilling_plan = []
                st.session_state.upskilling_raw_text = up_txt if up_txt else "无法生成计划"
            
            st.rerun()
    
    else:
        tab1, tab2, tab3 = st.tabs(["🌍 行业前景与 AI 风险", "📚 技能补全微课表", "💡 综合战略建议"])
        
        ind = st.session_state.industry_report or {}
        plan = st.session_state.upskilling_plan
        raw_text = st.session_state.upskilling_raw_text
        
        with tab1:
            render_score_metric("行业热度指数", ind.get('industry_score', 0))
            st.markdown(f"**📊 趋势研判:** {ind.get('industry_trend', '暂无数据')}")
            st.divider()
            st.subheader("🤖 AI 替代性风险评估")
            risk_lev = ind.get('ai_risk_level', '未知')
            risk_score = 90 if risk_lev == '低' else (50 if risk_lev == '中' else 20)
            render_score_metric(f"AI 风险等级 ({risk_lev})", risk_score)
            st.warning(ind.get('ai_risk_detail', ''))
            st.divider()
            st.subheader("🔄 类似岗位推荐")
            for role in ind.get('similar_roles', []):
                st.markdown(f"**{role['title']}**: {role['reason']}")
        
        with tab2:
            if raw_text:
                st.warning("⚠️ 格式化解析稍有问题，以下是 AI 生成的原始详细计划：")
                st.markdown(raw_text)
            elif not plan:
                st.info("暂未生成具体计划。")
            else:
                for i, item in enumerate(plan):
                    with st.expander(f"🎯 攻克差距：{item.get('gap', '未知')}", expanded=True):
                        st.markdown(f"**⏱️ 预计耗时:** {item.get('hours', '?')}")
                        st.markdown(f"**🔍 搜索关键词:** `{item.get('keywords', '')}`")
                        st.markdown("**📚 学习路径:**")
                        for step in item.get('path', []):
                            st.write(f"   - {step}")
                        st.success(f"**⚡ 微型实战:** {item.get('project', '')}")
        
        with tab3:
            st.subheader("💡 综合战略发展建议")
            raw_advice = ind.get('strategic_advice', '暂无')
            raw_pers_advice = st.session_state.personality_analysis.get('advice', '')
            
            if raw_advice:
                st.markdown("#### 🚀 行业与职业发展")
                st.info(body=raw_advice, icon="💡")
            
            st.divider()
            
            if raw_pers_advice:
                st.markdown("#### 🧩 性格与团队融合")
                st.success(body=raw_pers_advice, icon="🤝")
            
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        st.divider()
        nav_buttons(2, 4)

# ================= Step 4: 战略简历生成 & 提前下载 & 提前重置 =================
elif st.session_state.step == 4:
    st.subheader("4. 📄 战略级求职材料生成")
    
    if not st.session_state.final_resume:
        with st.spinner("AI 正在结合行业趋势与你的优势撰写详细简历..."):
            prompt_res = f"""
            生成一份详尽的战略级简历和求职信。
            背景：JD={st.session_state.persist_jd}, 简历={st.session_state.persist_resume}, 
            优势={st.session_state.skill_analysis.get('strengths')}, 
            行业趋势={st.session_state.industry_report.get('industry_trend') if st.session_state.industry_report else ''},
            性格建议={st.session_state.personality_analysis.get('advice')}
            要求：Markdown 格式，内容要丰富，不要省略细节。
            """
            content = call_deepseek([{"role": "user", "content": prompt_res}], current_api_key, DEFAULT_BASE_URL)
            if content:
                st.session_state.final_resume = content
                st.rerun()
            elif content is None:
                st.stop() # API 错误
    
    else:
        st.markdown(st.session_state.final_resume)
        
        st.divider()
        st.markdown("### 📥 阶段一：下载完整战略报告 (不含面试)")
        st.info("此报告包含：基础信息、匹配度分析、行业前景、技能补全计划、优化简历。**不含面试内容**。")
        
        report_content_txt = f"""
# AI 职业战略分析报告
**生成时间:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}

## 1. 基础信息
- **岗位:** {st.session_state.persist_jd[:100]}...
- **MBTI:** {st.session_state.persist_mbti}
- **硬性要求:** {st.session_state.persist_location}

## 2. 匹配度分析
- **硬技能得分:** {st.session_state.skill_analysis.get('score')}
- **性格匹配得分:** {st.session_state.personality_analysis.get('score')}
- **核心优势:** {st.session_state.skill_analysis.get('strengths')}
- **风险提示:** {st.session_state.personality_analysis.get('risk_alerts')}

## 3. 行业与战略
- **行业热度:** {st.session_state.industry_report.get('industry_score') if st.session_state.industry_report else 'N/A'}
- **AI 风险:** {st.session_state.industry_report.get('ai_risk_level') if st.session_state.industry_report else 'N/A'}
- **战略建议:** {st.session_state.industry_report.get('strategic_advice') if st.session_state.industry_report else 'N/A'}

## 4. 技能补全计划
{json.dumps(st.session_state.upskilling_plan, ensure_ascii=False, indent=2) if st.session_state.upskilling_plan else st.session_state.upskilling_raw_text}

## 5. 优化后简历内容
{st.session_state.final_resume}
        """
        
        report_content_doc = generate_doc_content(report_content_txt, "AI 职业战略分析报告")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                label="📥 下载战略报告 (.txt)",
                data=report_content_txt,
                file_name="Career_Strategy_Report.txt",
                mime="text/plain",
                type="primary",
                use_container_width=True
            )
        with c2:
            st.download_button(
                label="📥 下载战略报告 (.doc)",
                data=report_content_doc,
                file_name="Career_Strategy_Report.doc",
                mime="application/msword",
                type="primary",
                use_container_width=True
            )
        with c3:
            if st.button("🔄 重新开始 (保留画像)", type="secondary", use_container_width=True):
                st.session_state.step = 1
                st.session_state.persist_jd = ""
                st.session_state.skill_analysis = None
                st.session_state.personality_analysis = None
                st.session_state.industry_report = None
                st.session_state.upskilling_plan = None
                st.session_state.upskilling_raw_text = ""
                st.session_state.final_resume = ""
                st.session_state.interview_questions = None
                st.session_state.interview_feedback = {}
                st.session_state.user_answers = {}
                st.rerun()
        
        st.divider()
        if st.button("进入模拟面试环节 ➡️", type="primary", use_container_width=True):
            st.session_state.step = 5
            st.rerun()
        
        nav_buttons(3, None)

# ================= Step 5: 模拟面试 (多选项下载) =================
elif st.session_state.step == 5:
    st.subheader("5. 🎤 AI 模拟面试教练")
    st.markdown("此环节独立于主报告，专注于实战演练。")
    
    if st.session_state.interview_questions is None:
        with st.spinner("生成定制化面试题..."):
            gaps = st.session_state.skill_analysis.get('gaps', [])
            prompt_q = f"""
            基于 JD 和候选人差距，出 3 个刁钻面试题。
            JD: {st.session_state.persist_jd}
            差距：{gaps}
            返回 JSON: {{'questions': ['q1', 'q2', 'q3']}}
            """
            res = call_deepseek([{"role": "user", "content": prompt_q}], current_api_key, DEFAULT_BASE_URL)
            if res is None:
                st.stop()
            data = safe_json_loads(res)
            if data:
                st.session_state.interview_questions = data['questions']
                st.rerun()
    
    else:
        questions = st.session_state.interview_questions
        
        for i, q in enumerate(questions):
            st.markdown(f"**❓ 问题 {i+1}:** {q}")
            if str(i) not in st.session_state.user_answers:
                st.session_state.user_answers[str(i)] = ""
            
            ans = st.text_area(f"回答 {i+1}", value=st.session_state.user_answers[str(i)], key=f"ta_{i}", height=100)
            st.session_state.user_answers[str(i)] = ans
            
            if st.button(f"点评问题 {i+1}", key=f"btn_fb_{i}"):
                if not ans:
                    st.warning("请先输入回答")
                else:
                    with st.spinner("AI 毒舌点评中..."):
                        prompt_fb = f"""
                        面试点评。
                        问题：{q}
                        回答：{ans}
                        岗位：{st.session_state.persist_jd}
                        要求：Markdown 格式。1.评分 (0-10) 2.致命弱点 3.满分范文 (STAR)。
                        """
                        fb = call_deepseek([{"role": "user", "content": prompt_fb}], current_api_key, DEFAULT_BASE_URL)
                        if fb:
                            st.session_state.interview_feedback[str(i)] = fb
                            st.rerun()
                        else:
                            st.stop()
        
        st.divider()
        st.markdown("### 💬 点评详情")
        for i in range(len(questions)):
            key = str(i)
            if key in st.session_state.interview_feedback:
                with st.expander(f"问题 {i+1} 点评", expanded=True):
                    st.markdown(st.session_state.interview_feedback[key])
            else:
                st.info(f"问题 {i+1} 尚未点评。")
        
        st.divider()
        st.markdown("### 📥 阶段二：下载报告选项")
        
        interview_report_txt = f"""
# AI 模拟面试实战报告
**日期:** {datetime.datetime.now().strftime('%Y-%m-%d')}
**岗位:** {st.session_state.persist_jd[:50]}...

"""
        for i, q in enumerate(questions):
            key = str(i)
            interview_report_txt += f"""
## 问题 {i+1}
**Q:** {q}

**A (用户):** 
{st.session_state.user_answers.get(key, '')}

**🤖 AI 点评:** 
{st.session_state.interview_feedback.get(key, '待点评')}

---
"""
        interview_report_doc = generate_doc_content(interview_report_txt, "AI 模拟面试实战报告")

        full_report_txt = f"""
# AI 职业战略与面试全景报告
**生成时间:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}

## 第一部分：战略分析 (见上文)
- **岗位:** {st.session_state.persist_jd[:100]}...
- **硬技能得分:** {st.session_state.skill_analysis.get('score')}
- **性格匹配得分:** {st.session_state.personality_analysis.get('score')}
- **行业热度:** {st.session_state.industry_report.get('industry_score') if st.session_state.industry_report else 'N/A'}
- **战略建议:** {st.session_state.industry_report.get('strategic_advice') if st.session_state.industry_report else 'N/A'}
- **优化简历:** 
{st.session_state.final_resume}

## 第二部分：模拟面试实战
{interview_report_txt}
"""
        full_report_doc = generate_doc_content(full_report_txt, "AI 职业战略与面试全景报告")

        st.markdown("#### 选项 A: 仅下载面试部分")
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(label="📥 面试报告 (.txt)", data=interview_report_txt, file_name="Interview_Only.txt", mime="text/plain", use_container_width=True)
        with c2:
            st.download_button(label="📥 面试报告 (.doc)", data=interview_report_doc, file_name="Interview_Only.doc", mime="application/msword", use_container_width=True)

        st.markdown("#### 选项 B: 下载全部内容 (战略 + 面试)")
        c3, c4 = st.columns(2)
        with c3:
            st.download_button(label="📥 完整全景报告 (.txt)", data=full_report_txt, file_name="Full_Career_Report.txt", mime="text/plain", type="primary", use_container_width=True)
        with c4:
            st.download_button(label="📥 完整全景报告 (.doc)", data=full_report_doc, file_name="Full_Career_Report.doc", mime="application/msword", type="primary", use_container_width=True)

        st.divider()
        c5, c6 = st.columns(2)
        with c5:
             if st.button("🔄 重新开始 (保留画像&简历)", type="secondary", use_container_width=True):
                st.session_state.step = 1
                st.session_state.persist_jd = ""
                st.session_state.skill_analysis = None
                st.session_state.personality_analysis = None
                st.session_state.industry_report = None
                st.session_state.upskilling_plan = None
                st.session_state.upskilling_raw_text = ""
                st.session_state.final_resume = ""
                st.session_state.interview_questions = None
                st.session_state.interview_feedback = {}
                st.session_state.user_answers = {}
                st.rerun()
        
        nav_buttons(4, None)
