import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ui.report_config import is_section_visible, is_metric_visible

def _render_reach_impression_gap_section(period_result, report_key="report"):
    if not is_section_visible("reach_impression_gap") or not period_result: return
    cumulative=period_result.get("cumulative", {})
    items=[]
    if is_metric_visible("impressions"):
        items.append(("インプレッション", int(cumulative.get("impressions",0) or 0), "#FF6B00"))
    if is_metric_visible("reach"):
        items.append(("リーチ", int(cumulative.get("reach",0) or 0), "#7B2CFF"))
    if not items: return
    st.subheader("累計 リーチ・インプレッション")
    df=pd.DataFrame({"指標":[x[0] for x in items],"値":[x[1] for x in items],"色":[x[2] for x in items]})
    fig=go.Figure(go.Bar(x=df["値"],y=df["指標"],orientation="h",marker=dict(color=df["色"]),text=[f"{v:,}" for v in df["値"]],textposition="outside",hovertemplate="%{y}<br>%{x:,}<extra></extra>"))
    fig.update_layout(height=180+70*len(items),margin=dict(l=20,r=60,t=10,b=20),showlegend=False,plot_bgcolor="white",paper_bgcolor="white",bargap=0.35)
    fig.update_xaxes(rangemode="tozero",fixedrange=True,gridcolor="rgba(180,180,180,0.20)")
    fig.update_yaxes(fixedrange=True)
    st.plotly_chart(fig,width="stretch",key=f"{report_key}_reach_impression_gap_chart",config={"displayModeBar":False,"scrollZoom":False})
    if is_metric_visible("impressions"):
        frequency=float(cumulative.get("frequency",0) or 0)
        st.markdown(f"### 1人あたり平均表示回数：{frequency:.2f}回")
    st.divider()
