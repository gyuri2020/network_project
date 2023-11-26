#include <linux/module.h>
#include <linux/kernel.h>
#include <net/tcp.h>

void tcp_reno_init(struct sock *sk)
{
    /* 혼잡 제어와 관련된 변수 초기화 */
    tcp_sk(sk)->snd_ssthresh = 65535; // 보통 높은 값을 가짐
    tcp_sk(sk)->snd_cwnd = 10; // 초반 혼잡 윈도우를 10으로 설정
}

u32 tcp_reno_ssthresh(struct sock *sk)
{
    /* 혼잡 윈도우 절반으로 줄임 */
    const struct tcp_sock *tp = tcp_sk(sk);
    return max(tp->snd_cwnd >> 1U, 2U);
}

void tcp_reno_cong_avoid(struct sock *sk, u32 ack, u32 acked)
{
    struct tcp_sock *tp = tcp_sk(sk);

    if (!tcp_is_cwnd_limited(sk))
        return;

    if (tp->snd_cwnd <= tp->snd_ssthresh) {
        /* "느린 시작" 상태에서 ACK된 패킷 수만큼 혼잡 윈도우 크기 증가 */
        acked = tcp_slow_start(tp, acked);
        if (!acked)
            return;
    } else {
        /* "혼잡 회피" 상태에서 혼잡 윈도우 크기 증가
         * RTT(왕복 시간)를 대략적으로 나눈 것으로 패킷 크기를 증가시킴 */
        tcp_cong_avoid_ai(tp, tp->snd_cwnd, acked);
    }

    /* 혼잡 윈도우 크기가 최대 허용 값보다 크지 않도록 조정 */
    tp->snd_cwnd = min(tp->snd_cwnd, tp->snd_cwnd_clamp);
}

u32 tcp_reno_undo_cwnd(struct sock *sk)
{
    /* 혼잡 회피 중 변경된 혼잡 윈도우 크기를 되돌림 */
    return tcp_sk(sk)->snd_cwnd;
}

/* 혼잡 제어 알고리즘을 위한 훅을 포함하는 구조체 */
static struct tcp_congestion_ops tcp_reno_custom = {
    .init           = tcp_reno_init,
    .ssthresh       = tcp_reno_ssthresh,
    .cong_avoid     = tcp_reno_cong_avoid,
    .undo_cwnd      = tcp_reno_undo_cwnd,

    .owner          = THIS_MODULE,
    .name           = "reno_custom",
};

/* 모듈 초기화 함수 */
static int __init tcp_reno_module_init(void)
{
    /* 새로운 혼잡 제어 등록 */
    BUILD_BUG_ON(sizeof(struct tcp_congestion_ops) != sizeof(struct tcp_congestion_ops));
    if (tcp_register_congestion_control(&tcp_reno_custom))
        return -ENOBUFS;
    return 0;
}

/* 모듈 정리 함수 */
static void __exit tcp_reno_module_exit(void)
{
    /* 혼잡 제어 등록 해제 */
    tcp_unregister_congestion_control(&tcp_reno_custom);
}

module_init(tcp_reno_module_init);
module_exit(tcp_reno_module_exit);

MODULE_AUTHOR("nethw");
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("TCP Reno Congestion Control");
