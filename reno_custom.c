#include <linux/module.h>
#include <linux/kernel.h>
#include <net/tcp.h>

void tcp_reno_init(struct sock *sk)
{
    /* Initialize congestion control specific variables here */
    tcp_sk(sk)->snd_ssthresh = TCP_INFINITE_SSTHRESH; // Typically, this is a high value
    tcp_sk(sk)->snd_cwnd = 3;                         // Start with a congestion window of 3
}

u32 tcp_reno_ssthresh(struct sock *sk)
{
    /* Halve the congestion window, min 2 */
    const struct tcp_sock *tp = tcp_sk(sk);
    u32 new_ssthresh = tp->snd_cwnd >> 1U;
    u32 addition = (new_ssthresh > 2U) ? (new_ssthresh >> 1U) : 1U;

    return max(new_ssthresh + addition, 2U);
}

void tcp_custom_cong_avoid_ai(struct tcp_sock *tp, u32 w, u32 acked)
{

    tp->snd_cwnd_cnt += acked;

    if (tp->snd_cwnd_cnt >= w)
    {
        u32 extra_credits = tp->snd_cwnd_cnt / w;
        tp->snd_cwnd_cnt -= extra_credits * w;
        tp->snd_cwnd += extra_credits;
    }

    tp->snd_cwnd = min(tp->snd_cwnd, tp->snd_cwnd_clamp);
}

void tcp_custom_fast_recovery(struct tcp_sock *tp, u32 acked)
{
    tp->snd_cwnd_cnt += (acked + 1);

    if (tp->snd_cwnd_cnt >= tp->snd_cwnd)
    {
        u32 extra_credits = tp->snd_cwnd_cnt / tp->snd_cwnd;
        tp->snd_cwnd_cnt -= extra_credits * tp->snd_cwnd;
        tp->snd_cwnd += extra_credits;
    }

    tp->snd_cwnd = min(tp->snd_cwnd, tp->snd_cwnd_clamp);
}

void tcp_reno_cong_avoid(struct sock *sk, u32 ack, u32 acked)
{
    struct tcp_sock *tp = tcp_sk(sk);

    if (!tcp_is_cwnd_limited(sk))
        return;

    if (tp->snd_cwnd <= tp->snd_ssthresh)
    {
        /* In "slow start", cwnd is increased by the number of ACKed packets */
        acked = tcp_slow_start(tp, acked);
        if (!acked)
            return;
    }
    else if (tp->snd_cwnd < 2 * tp->snd_ssthresh)
    {
        tcp_custom_fast_recovery(tp, acked);
    }
    else
    {

        /* In "congestion avoidance", cwnd is increased by 1 full packet
         * per round-trip time (RTT), which is approximated here by the number of
         * ACKed packets divided by the current congestion window. */
        tcp_custom_cong_avoid_ai(tp, tp->snd_cwnd, acked);
    }

    /* Ensure that cwnd does not exceed the maximum allowed value */
    tp->snd_cwnd = min(tp->snd_cwnd, tp->snd_cwnd_clamp);
}

u32 tcp_reno_undo_cwnd(struct sock *sk)
{
    /* Undo the cwnd changes during congestion avoidance if needed */
    return tcp_sk(sk)->snd_cwnd;
}

/* This structure contains the hooks to our congestion control algorithm */
static struct tcp_congestion_ops tcp_reno_custom = {
    .init = tcp_reno_init,
    .ssthresh = tcp_reno_ssthresh,
    .cong_avoid = tcp_reno_cong_avoid,
    .undo_cwnd = tcp_reno_undo_cwnd,

    .owner = THIS_MODULE,
    .name = "reno_custom",
};

/* Initialization function of this module */
static int __init tcp_reno_module_init(void)
{
    /* Register the new congestion control */
    BUILD_BUG_ON(sizeof(struct tcp_congestion_ops) != sizeof(struct tcp_congestion_ops));
    if (tcp_register_congestion_control(&tcp_reno_custom))
        return -ENOBUFS;
    return 0;
}

/* Cleanup function of this module */
static void __exit tcp_reno_module_exit(void)
{
    /* Unregister the congestion control */
    tcp_unregister_congestion_control(&tcp_reno_custom);
}

module_init(tcp_reno_module_init);
module_exit(tcp_reno_module_exit);

MODULE_AUTHOR("nethw");
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("TCP Reno Congestion Control");
