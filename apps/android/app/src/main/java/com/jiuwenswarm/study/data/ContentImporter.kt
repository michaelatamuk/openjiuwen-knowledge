package com.jiuwenswarm.study.data

import android.content.Context
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

object ContentImporter {

    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }

    /** Import the bundled content.json into Room on first launch. */
    suspend fun importIfNeeded(context: Context, db: AppDatabase) {
        if (db.questions().count() > 0) return
        val text = context.assets.open("content.json").bufferedReader().use { it.readText() }
        val root = json.decodeFromString<ContentRoot>(text)

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
        db.topics().insertAll(topics)
        db.questions().insertAll(questions)
        db.cards().insertAll(cards)
    }
}
