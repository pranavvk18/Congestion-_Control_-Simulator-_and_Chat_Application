import streamlit as st
import matplotlib.pyplot as plt
import random
import pandas as pd
import time

st.set_page_config(layout="wide")
st.title("🕸️ Advanced TCP Congestion Control Simulator")

# Sidebar
algorithm = st.sidebar.selectbox("Choose Algorithm", ["Tahoe", "Reno", "NewReno"])
max_rounds = st.sidebar.slider("Rounds (RTTs)", 10, 200, 50)
packet_loss_prob = st.sidebar.slider("Packet Loss Probability", 0.0, 1.0, 0.1)
ssthresh_init = st.sidebar.slider("Initial ssthresh", 8, 64, 16)
min_rtt = st.sidebar.slider("Min RTT (ms)", 20, 200, 100)
max_rtt = st.sidebar.slider("Max RTT (ms)", 100, 500, 300)
buffer_size = st.sidebar.slider("Receiver Buffer Size", 5, 100, 32)

# Variables
cwnd = 1
ssthresh = ssthresh_init
fast_recovery = False
dup_acks = 0
buffer = 0

# Tracking
data = []

# Simulate
for i in range(max_rounds):
    rtt = random.randint(min_rtt, max_rtt)
    loss = random.random() < packet_loss_prob
    ack_received = False
    buffer_state = buffer

    if loss:
        ssthresh = max(cwnd // 2, 1)
        if algorithm == "Tahoe":
            cwnd = 1
            fast_recovery = False
        elif algorithm == "Reno":
            if not fast_recovery:
                cwnd = ssthresh
                fast_recovery = True
            else:
                cwnd = 1
                fast_recovery = False
        elif algorithm == "NewReno":
            if not fast_recovery:
                fast_recovery = True
                cwnd = ssthresh
            else:
                cwnd -= 1
        ack_received = False
        dup_acks += 1
    else:
        dup_acks = 0
        ack_received = True
        if cwnd < ssthresh:
            cwnd *= 2  # slow start
        else:
            cwnd += 1  # congestion avoidance
        fast_recovery = False

    buffer = min(buffer + cwnd, buffer_size)
    buffer = max(buffer - 1, 0)  # simulate ACK draining

    # Store data
    data.append({
        "RTT (ms)": rtt,
        "Round": i,
        "cwnd": cwnd,
        "ssthresh": ssthresh,
        "Packet Loss": loss,
        "ACK Received": ack_received,
        "Receive Buffer": buffer_state
    })

# Convert to DataFrame
df = pd.DataFrame(data)

# Plot
tab1, tab2 = st.tabs(["📈 Congestion Window", "📥 Buffer & RTT"])

with tab1:
    fig, ax = plt.subplots()
    ax.plot(df["Round"], df["cwnd"], label="cwnd", marker='o')
    ax.plot(df["Round"], df["ssthresh"], label="ssthresh", linestyle='--')
    ax.set_title(f"TCP {algorithm} Congestion Control")
    ax.set_xlabel("RTT Round")
    ax.set_ylabel("Window Size")
    ax.legend()
    st.pyplot(fig)

with tab2:
    fig2, ax2 = plt.subplots()
    ax2.plot(df["Round"], df["Receive Buffer"], label="Buffer Usage")
    ax2.plot(df["Round"], df["RTT (ms)"], label="RTT (ms)", linestyle='--')
    ax2.set_title("Buffer and RTT Variation")
    ax2.set_xlabel("RTT Round")
    ax2.legend()
    st.pyplot(fig2)

# Export
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download CSV Results", data=csv, file_name='tcp_simulation.csv', mime='text/csv')

# Table
with st.expander("📊 Simulation Data Table"):
    st.dataframe(df)
