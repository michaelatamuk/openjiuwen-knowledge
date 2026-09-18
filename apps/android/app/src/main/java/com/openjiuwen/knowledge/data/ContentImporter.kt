package com.openjiuwen.knowledge.data

import android.content.Context
import androidx.room.withTransaction
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.security.MessageDigest

object ContentImporter {

    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }
    private const val PREFS = "content"
    private const val KEY_HASH = "content_hash"

    /**
     * Import the bundled content.json into Room when it is absent or has changed
     * since the last import. Study progress (card scheduling) is preserved for
     * questions that still exist.
     */
    suspend fun importIfNeeded(context: Context, db: AppDatabase) {
        val bytes = context.assets.open("content.json").use { it.readBytes() }
        val hash = MessageDigest.getInstance("SHA-1").digest(bytes)
            .joinToString("") { "%02x".format(it) }
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        if (prefs.getString(KEY_HASH, null) == hash && db.questions().count() > 0) return

        val root = json.decodeFromString<ContentRoot>(String(bytes, Charsets.UTF_8))

        val topics = root.topics.mapIndexed { i, t -> TopicEntity(t.id, t.title, i, t.section) }
        val questions = ArrayList<QuestionEntity>()
        val cards = ArrayList<CardEntity>()
        for (t in root.topics) {
            for (q in t.questions) {
                val blob = buildString {
                    append(q.question).append('\n')
                    append(q.tldr).append('\n')
                    append(q.points.joinToString("\n")).append('\n')
                    append(q.explain).append('\n')
                    append(q.mechanism).append('\n')
                    append(q.citations.joinToString("\n") { it.ref + " " + it.desc })
                }
                questions.add(
                    QuestionEntity(
                        id = q.id, topicId = q.topicId, number = q.number, type = q.type,
                        question = q.question, title = q.title, tldr = q.tldr,
                        pointsJson = json.encodeToString(q.points),
                        explain = q.explain, mechanism = q.mechanism, jiuwenPlain = q.jiuwenPlain,
                        citationsJson = json.encodeToString(q.citations),
                        pitfallsJson = json.encodeToString(q.pitfalls),
                        followupsJson = json.encodeToString(q.followups),
                        diagramSvg = q.diagram.svg, diagramImage = q.diagram.image,
                        diagramSvgDark = q.diagram.svgDark,
                        diagramW = q.diagram.width, diagramH = q.diagram.height,
                        diagramAlt = q.diagram.alt, diagramSource = q.diagram.source,
                        diagramStepsJson = json.encodeToString(q.diagram.steps),
                        diagramNodesJson = json.encodeToString(q.diagram.nodes),
                        diagramListJson = json.encodeToString(q.diagrams),
                        diagramTechJson = json.encodeToString(q.diagramTechnical),
                        metaJson = json.encodeToString(q.meta),
                        provenanceJson = json.encodeToString(q.provenance),
                        searchBlob = blob,
                    )
                )
                cards.add(CardEntity(questionId = q.id))
            }
        }

        val prior = db.cards().all().associateBy { it.questionId }
        db.withTransaction {
            db.topics().clear()
            db.questions().clear()
            db.cards().clear()
            db.topics().insertAll(topics)
            db.questions().insertAll(questions)
            db.cards().insertAll(cards.map { prior[it.questionId] ?: it })
        }
        prefs.edit().putString(KEY_HASH, hash).apply()
    }
}
