package com.openjiuwen.knowledge.data

import kotlinx.serialization.Serializable

@Serializable
data class ContentRoot(
    val version: Int = 2,
    val topics: List<TopicDto> = emptyList(),
)

@Serializable
data class TopicDto(
    val id: String,
    val title: String,
    val section: String = "",
    val questions: List<QuestionDto> = emptyList(),
)

@Serializable
data class QuestionDto(
    val id: String,
    val topicId: String,
    val topicTitle: String,
    val number: Int,
    val type: String = "concept",
    val question: String,
    val title: String = "",
    val tldr: String = "",
    val points: List<String> = emptyList(),
    val explain: String = "",
    val mechanism: String = "",
    val jiuwenPlain: String = "",
    val citations: List<CitationDto> = emptyList(),
    val pitfalls: List<String> = emptyList(),
    val followups: List<String> = emptyList(),
    val diagram: DiagramDto = DiagramDto(),
    val diagrams: List<DiagramDto> = emptyList(),
    val diagramTechnical: DiagramDto = DiagramDto(),
    val meta: MetaDto = MetaDto(),
    val provenance: ProvenanceDto = ProvenanceDto(),
)

@Serializable
data class CitationDto(
    val kind: String = "code",
    val ref: String,
    val symbol: String = "",
    val lines: String = "",
    val desc: String = "",
    val snippet: String = "",
)

@Serializable
data class DiagramDto(
    val source: String = "",
    val svg: String = "",
    val image: String = "",
    val svgDark: String = "",
    val width: Float = 0f,
    val height: Float = 0f,
    val alt: String = "",
    val steps: List<String> = emptyList(),
    val nodes: List<DiagramNodeDto> = emptyList(),
)

@Serializable
data class DiagramNodeDto(
    val label: String = "",
    val x: Float = 0f,
    val y: Float = 0f,
)

@Serializable
data class MetaDto(
    val difficulty: String = "core",
    val tags: List<String> = emptyList(),
    val related: List<String> = emptyList(),
)

@Serializable
data class ProvenanceDto(
    val sources: List<String> = emptyList(),
    val reviewedAt: String = "",
)
