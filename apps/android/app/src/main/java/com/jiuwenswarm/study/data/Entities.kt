package com.jiuwenswarm.study.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "topics")
data class TopicEntity(
    @PrimaryKey val id: String,
    val title: String,
    val orderIndex: Int,
)

/** A question as a layered/atomic topic page (v2 schema). */
@Entity(tableName = "questions")
data class QuestionEntity(
    @PrimaryKey val id: String,
    val topicId: String,
    val number: Int,
    val type: String,
    val question: String,
    val title: String,
    val tldr: String,
    val pointsJson: String,
    val explain: String,
    val mechanism: String,
    val jiuwenPlain: String,
    val citationsJson: String,
    val pitfallsJson: String,
    val followupsJson: String,
    val diagramSvg: String,
    val diagramImage: String,
    val diagramSvgDark: String,
    val diagramW: Float,
    val diagramH: Float,
    val diagramAlt: String,
    val diagramSource: String,
    val diagramStepsJson: String,
    val diagramNodesJson: String,
    val diagramListJson: String,
    val diagramTechJson: String,
    val metaJson: String,
    val provenanceJson: String,
    val searchBlob: String,
)

/** Spaced-repetition state for one question (FSRS). */
@Entity(tableName = "cards")
data class CardEntity(
    @PrimaryKey val questionId: String,
    val state: Int = 0,
    val stability: Double = 0.0,
    val difficulty: Double = 0.0,
    val due: Long = 0L,
    val lastReview: Long = 0L,
    val reps: Int = 0,
    val lapses: Int = 0,
    val elapsedDays: Double = 0.0,
    val scheduledDays: Double = 0.0,
)

@Entity(tableName = "notes")
data class NoteEntity(
    @PrimaryKey val questionId: String,
    val text: String,
    val updatedAt: Long,
)

@Entity(tableName = "bookmarks")
data class BookmarkEntity(
    @PrimaryKey val questionId: String,
    val createdAt: Long,
)

@Entity(tableName = "review_log")
data class ReviewLogEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val questionId: String,
    val rating: Int,
    val reviewedAt: Long,
    val stateBefore: Int,
    val stateAfter: Int,
)
