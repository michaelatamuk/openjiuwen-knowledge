package com.jiuwenswarm.study.data

import kotlinx.coroutines.flow.Flow
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json

class Repo(private val db: AppDatabase) {

    val json = Json { ignoreUnknownKeys = true }

    val topics: Flow<List<TopicEntity>> = db.topics().observeAll()

    fun questionsForTopic(topicId: String): Flow<List<QuestionEntity>> =
        db.questions().observeByTopic(topicId)

    fun question(id: String): Flow<QuestionEntity?> = db.questions().observeById(id)

    fun card(id: String): Flow<CardEntity?> = db.cards().observeById(id)

    fun search(q: String): Flow<List<QuestionEntity>> = db.questions().search(q)

    fun dueCount(now: Long): Flow<Int> = db.cards().observeDueCount(now)
    fun newCount(): Flow<Int> = db.cards().observeNewCount()
    fun learnedCount(): Flow<Int> = db.cards().observeLearnedCount()
    fun mastery(): Flow<Double?> = db.cards().observeMastery()
    fun reviewsSince(since: Long): Flow<Int> = db.reviewLog().observeReviewsSince(since)
    fun totalReviews(): Flow<Int> = db.reviewLog().observeTotalReviews()
    fun activeDays(): Flow<Int> = db.reviewLog().observeActiveDays()

    // --- layered content accessors -------------------------------------------------

    fun points(q: QuestionEntity): List<String> = decodeList(q.pointsJson)

    fun pitfalls(q: QuestionEntity): List<String> = decodeList(q.pitfallsJson)

    fun followups(q: QuestionEntity): List<String> = decodeList(q.followupsJson)

    fun steps(q: QuestionEntity): List<String> = decodeList(q.diagramStepsJson)

    fun citations(q: QuestionEntity): List<CitationDto> =
        runCatching { json.decodeFromString<List<CitationDto>>(q.citationsJson) }.getOrDefault(emptyList())

    fun meta(q: QuestionEntity): MetaDto =
        runCatching { json.decodeFromString<MetaDto>(q.metaJson) }.getOrDefault(MetaDto())

    fun provenance(q: QuestionEntity): ProvenanceDto =
        runCatching { json.decodeFromString<ProvenanceDto>(q.provenanceJson) }.getOrDefault(ProvenanceDto())

    fun diagram(q: QuestionEntity): DiagramData? {
        if (q.diagramImage.isBlank() && q.diagramSvg.isBlank()) return null
        val nodes = runCatching { json.decodeFromString<List<DiagramNodeDto>>(q.diagramNodesJson) }
            .getOrDefault(emptyList())
        return DiagramData(
            svg = q.diagramSvg, image = q.diagramImage, svgDark = q.diagramSvgDark,
            w = q.diagramW, h = q.diagramH,
            alt = q.diagramAlt, steps = decodeList(q.diagramStepsJson), nodes = nodes,
        )
    }

    fun diagrams(q: QuestionEntity): List<DiagramData> {
        val list = runCatching { json.decodeFromString<List<DiagramDto>>(q.diagramListJson) }
            .getOrDefault(emptyList())
            .filter { it.image.isNotBlank() || it.svg.isNotBlank() }
            .map { DiagramData(it.svg, it.image, it.svgDark, it.width, it.height, it.alt, it.steps, it.nodes) }
        if (list.isNotEmpty()) return list
        return listOfNotNull(diagram(q))
    }

    fun diagramTechnical(q: QuestionEntity): DiagramData? {
        val d = runCatching { json.decodeFromString<DiagramDto>(q.diagramTechJson) }.getOrNull() ?: return null
        if (d.image.isBlank() && d.svg.isBlank()) return null
        return DiagramData(
            svg = d.svg, image = d.image, svgDark = d.svgDark, w = d.width, h = d.height,
            alt = d.alt, steps = d.steps, nodes = d.nodes,
        )
    }

    private inline fun <reified T> decodeList(s: String): List<T> =
        runCatching { json.decodeFromString<List<T>>(s) }.getOrDefault(emptyList())

    // --- bookmarks / notes ---------------------------------------------------------

    fun bookmarkIds(): Flow<List<String>> = db.bookmarks().observeIds()

    suspend fun toggleBookmark(questionId: String, on: Boolean) {
        if (on) db.bookmarks().remove(questionId)
        else db.bookmarks().add(BookmarkEntity(questionId, System.currentTimeMillis()))
    }

    fun note(questionId: String): Flow<NoteEntity?> = db.notes().observe(questionId)

    suspend fun saveNote(questionId: String, text: String) {
        if (text.isBlank()) db.notes().delete(questionId)
        else db.notes().upsert(NoteEntity(questionId, text, System.currentTimeMillis()))
    }

    // --- study ---------------------------------------------------------------------

    suspend fun buildQueue(maxDue: Int = 30, maxNew: Int = 8): List<StudyItem> {
        val now = System.currentTimeMillis()
        val out = ArrayList<StudyItem>()
        for (c in db.cards().dueCards(now, maxDue)) {
            db.questions().byId(c.questionId)?.let { out.add(StudyItem(it, c)) }
        }
        for (c in db.cards().newCards(maxNew)) {
            db.questions().byId(c.questionId)?.let { out.add(StudyItem(it, c)) }
        }
        return out
    }

    suspend fun rate(questionId: String, rating: Int) {
        val now = System.currentTimeMillis()
        val card = db.cards().byId(questionId) ?: CardEntity(questionId = questionId)
        val r = Fsrs.schedule(card, rating, now)
        db.cards().update(
            card.copy(
                state = r.state, stability = r.stability, difficulty = r.difficulty,
                due = r.due, lastReview = now, reps = r.reps, lapses = r.lapses,
                elapsedDays = r.elapsedDays, scheduledDays = r.scheduledDays,
            )
        )
        db.reviewLog().insert(
            ReviewLogEntity(
                questionId = questionId, rating = rating, reviewedAt = now,
                stateBefore = card.state, stateAfter = r.state,
            )
        )
    }
}

data class StudyItem(val question: QuestionEntity, val card: CardEntity)

data class DiagramData(
    val svg: String,
    val image: String,
    val svgDark: String,
    val w: Float,
    val h: Float,
    val alt: String,
    val steps: List<String>,
    val nodes: List<DiagramNodeDto>,
)
