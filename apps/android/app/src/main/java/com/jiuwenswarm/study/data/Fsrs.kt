package com.jiuwenswarm.study.data

import kotlin.math.exp
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow

/**
 * FSRS-5 scheduler (default parameters). Given a card and a 1..4 rating it
 * returns the next memory state and due time.
 */
object Fsrs {
    const val AGAIN = 1
    const val HARD = 2
    const val GOOD = 3
    const val EASY = 4

    const val STATE_NEW = 0
    const val STATE_LEARNING = 1
    const val STATE_REVIEW = 2
    const val STATE_RELEARNING = 3

    private val W = doubleArrayOf(
        0.40255, 1.18385, 3.173, 15.69105, 7.1949, 0.5345, 1.4604, 0.0046, 1.54575,
        0.1192, 1.01925, 1.9395, 0.11, 0.29605, 2.2698, 0.2315, 2.9898, 0.51655, 0.6621,
    )
    private const val DECAY = -0.5
    private const val FACTOR = 19.0 / 81.0
    private const val DAY = 86_400_000L
    private const val RELEARN_MS = 10 * 60_000L

    fun initStability(g: Int): Double = W[(g - 1).coerceIn(0, 3)]

    fun initDifficulty(g: Int): Double =
        (W[4] - exp(W[5] * (g - 1)) + 1).coerceIn(1.0, 10.0)

    fun retrievability(elapsedDays: Double, stability: Double): Double {
        if (stability <= 0.0) return 0.0
        return (1 + FACTOR * elapsedDays / stability).pow(DECAY)
    }

    fun intervalFromStability(stability: Double, retention: Double = 0.9): Double =
        (stability / FACTOR * (retention.pow(1.0 / DECAY) - 1)).coerceAtLeast(0.0)

    private fun nextDifficulty(d: Double, g: Int): Double =
        (W[7] * initDifficulty(EASY) + (1 - W[7]) * (d - W[6] * (g - 3))).coerceIn(1.0, 10.0)

    private fun recallStability(d: Double, s: Double, r: Double, g: Int): Double {
        val hard = if (g == HARD) W[15] else 1.0
        val easy = if (g == EASY) W[16] else 1.0
        return s * (1 + exp(W[8]) * (11 - d) * s.pow(-W[9]) * (exp(W[10] * (1 - r)) - 1) * hard * easy)
    }

    private fun forgetStability(d: Double, s: Double, r: Double): Double =
        (W[11] * d.pow(-W[12]) * ((s + 1).pow(W[13]) - 1) * exp(W[14] * (1 - r)))
            .coerceAtMost(s).coerceAtLeast(0.1)

    data class Result(
        val state: Int,
        val stability: Double,
        val difficulty: Double,
        val due: Long,
        val reps: Int,
        val lapses: Int,
        val elapsedDays: Double,
        val scheduledDays: Double,
    )

    fun schedule(card: CardEntity, rating: Int, now: Long): Result {
        val g = rating.coerceIn(1, 4)
        if (card.reps == 0) {
            val s = initStability(g)
            val d = initDifficulty(g)
            return if (g == AGAIN) {
                Result(STATE_LEARNING, s, d, now + RELEARN_MS, 1, 0, 0.0, 0.0)
            } else {
                val days = max(1.0, intervalFromStability(s))
                Result(STATE_REVIEW, s, d, now + days.toLong() * DAY, 1, 0, 0.0, days)
            }
        }
        val elapsed = if (card.lastReview > 0) (now - card.lastReview).toDouble() / DAY else 0.0
        val r = retrievability(elapsed, card.stability)
        val d = nextDifficulty(card.difficulty, g)
        return if (g == AGAIN) {
            val s = forgetStability(card.difficulty, card.stability, r)
            Result(STATE_RELEARNING, s, d, now + RELEARN_MS, card.reps + 1, card.lapses + 1, elapsed, 0.0)
        } else {
            val s = recallStability(card.difficulty, card.stability, r, g)
            var days = max(1.0, intervalFromStability(s))
            if (g == HARD) days = min(days, max(1.0, card.scheduledDays))
            Result(STATE_REVIEW, s, d, now + days.toLong() * DAY, card.reps + 1, card.lapses, elapsed, days)
        }
    }
}
