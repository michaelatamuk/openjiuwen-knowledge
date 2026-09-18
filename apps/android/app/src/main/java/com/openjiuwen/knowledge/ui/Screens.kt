package com.openjiuwen.knowledge.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bookmark
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Sort
import androidx.compose.material.icons.outlined.BookmarkBorder
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.openjiuwen.knowledge.data.MetaDto
import com.openjiuwen.knowledge.data.QuestionEntity
import com.openjiuwen.knowledge.data.Repo
import com.openjiuwen.knowledge.data.StudyItem
import kotlinx.coroutines.launch

@Composable
private fun Section(title: String, body: String) {
    if (body.isBlank()) return
    Column(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
        Text(title, style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.primary)
        Spacer(Modifier.height(4.dp))
        MarkdownText(body)
    }
}

@Composable
private fun BulletList(title: String, items: List<String>) {
    if (items.isEmpty()) return
    Column(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
        Text(title, style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.primary)
        Spacer(Modifier.height(4.dp))
        items.forEach { Text("• $it", style = MaterialTheme.typography.bodyLarge) }
    }
}

// ---------------------------------------------------------------- Today

@Composable
fun TodayScreen(repo: Repo, onStudy: () -> Unit, onExplore: () -> Unit) {
    val now = remember { System.currentTimeMillis() }
    val due by repo.dueCount(now).collectAsStateWithLifecycle(0)
    val new by repo.newCount().collectAsStateWithLifecycle(0)
    val learned by repo.learnedCount().collectAsStateWithLifecycle(0)
    val days by repo.activeDays().collectAsStateWithLifecycle(0)
    val total by repo.totalReviews().collectAsStateWithLifecycle(0)

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("Today", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        val todo = due + new
        Card(Modifier.fillMaxWidth()) {
            Row(Modifier.padding(20.dp), verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(96.dp), contentAlignment = Alignment.Center) {
                    ProgressRing(if (todo == 0) 1f else 0f)
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("$due", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                        Text("due", style = MaterialTheme.typography.labelSmall)
                    }
                }
                Spacer(Modifier.width(20.dp))
                Column(Modifier.weight(1f)) {
                    Text(if (todo == 0) "All caught up" else "$todo cards to review",
                        style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(4.dp))
                    Text("$new new · $learned learned", style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
        Button(onClick = onStudy, Modifier.fillMaxWidth().height(56.dp)) {
            Text(if (todo == 0) "Practice anyway" else "Start review", style = MaterialTheme.typography.titleMedium)
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            StatCard("Streak", "$days d", Modifier.weight(1f))
            StatCard("Reviews", "$total", Modifier.weight(1f))
        }
        OutlinedButton(onClick = onExplore, Modifier.fillMaxWidth()) { Text("Explore topics") }
    }
}

@Composable
private fun StatCard(label: String, value: String, modifier: Modifier = Modifier) {
    Card(modifier) {
        Column(Modifier.padding(16.dp)) {
            Text(value, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text(label, style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

// ---------------------------------------------------------------- Study

@Composable
fun StudyScreen(repo: Repo, onOpen: (String) -> Unit) {
    val scope = rememberCoroutineScope()
    var queue by remember { mutableStateOf<List<StudyItem>?>(null) }
    var index by remember { mutableIntStateOf(0) }
    var reveal by remember { mutableIntStateOf(0) }

    LaunchedEffect(Unit) { queue = repo.buildQueue() }

    val q = queue
    if (q == null) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text("Loading…") }
        return
    }
    if (index >= q.size) {
        Column(Modifier.fillMaxSize().padding(24.dp),
            verticalArrangement = Arrangement.Center, horizontalAlignment = Alignment.CenterHorizontally) {
            Text("Done for now", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(8.dp))
            Text("Reviewed ${q.size} cards.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        return
    }

    val item = q[index]
    val points = remember(item) { repo.points(item.question) }
    val pitfalls = remember(item) { repo.pitfalls(item.question) }
    val citations = remember(item) { repo.citations(item.question) }
    val diagrams = remember(item) { repo.diagrams(item.question) }
    val techDiagram = remember(item) { repo.diagramTechnical(item.question) }

    Column(Modifier.fillMaxSize().padding(20.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("${index + 1} / ${q.size}", style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.weight(1f))
            TypeBadge(item.question.type)
        }
        Spacer(Modifier.height(8.dp))
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState())) {
            Text(item.question.question, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(12.dp))

            if (reveal >= 1) {
                if (item.question.tldr.isNotBlank()) {
                    Text("TL;DR", style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                    Spacer(Modifier.height(2.dp))
                    Text(item.question.tldr, style = MaterialTheme.typography.bodyMedium)
                }
                Spacer(Modifier.height(8.dp))
                PointsList(points)
            }
            if (reveal >= 2) {
                Section("Concept", item.question.explain)
                diagrams.forEach { d ->
                    Spacer(Modifier.height(8.dp))
                    DiagramView(d, citations)
                }
                BulletList("Pitfalls", pitfalls)
            }
            if (reveal >= 3) {
                val plainJ = item.question.jiuwenPlain
                Section("In Jiuwen", plainJ.ifBlank { item.question.mechanism })
                TechnicalDetail(if (plainJ.isBlank()) "" else item.question.mechanism, citations, techDiagram, repo.provenance(item.question).sources)
                TextButton(onClick = { onOpen(item.question.id) }) { Text("Open full topic page") }
            }
        }
        Spacer(Modifier.height(12.dp))
        if (reveal < 3) {
            Button(onClick = { reveal++ }, Modifier.fillMaxWidth().height(52.dp)) {
                Text(if (reveal == 0) "Show answer" else "Show more")
            }
        } else {
            RatingBar { rating ->
                scope.launch { repo.rate(item.question.id, rating); index++; reveal = 0 }
            }
        }
    }
}

// ---------------------------------------------------------------- Explore

@Composable
fun ExploreScreen(repo: Repo, onTopic: (String) -> Unit) {
    val topics by repo.topics.collectAsStateWithLifecycle(emptyList())
    val grouped = topics.groupBy { it.section.ifBlank { "Other" } }
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item { Text("Topics", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold) }
        grouped.forEach { (section, items) ->
            item(key = "section-$section") {
                Text(section, style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(top = 8.dp))
            }
            items(items, key = { it.id }) { t ->
                Card(Modifier.fillMaxWidth().clickable { onTopic(t.id) }) {
                    Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                        Text(t.id, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary)
                        Spacer(Modifier.width(14.dp))
                        Text(t.title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                    }
                }
            }
        }
    }
}

private fun difficultyRank(d: String): Int = when (d.lowercase()) {
    "basic" -> 0
    "intermediate" -> 1
    "advanced" -> 2
    else -> 3
}

@Composable
private fun DifficultyText(difficulty: String) {
    if (difficulty.isBlank()) return
    val color = when (difficulty.lowercase()) {
        "basic" -> Color(0xFF2E7D32)
        "intermediate" -> Color(0xFFB26A00)
        "advanced" -> Color(0xFFC62828)
        else -> MaterialTheme.colorScheme.onSurfaceVariant
    }
    Text(difficulty.replaceFirstChar { it.uppercase() },
        style = MaterialTheme.typography.labelSmall, color = color)
}

@Composable
private fun MetaLine(type: String, difficulty: String) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        if (type.isNotBlank()) TypeBadge(type)
        DifficultyText(difficulty)
    }
}

@Composable
fun TopicScreen(repo: Repo, topicId: String, onQuestion: (String) -> Unit) {
    val questions by repo.questionsForTopic(topicId).collectAsStateWithLifecycle(emptyList())
    val topics by repo.topics.collectAsStateWithLifecycle(emptyList())
    val topic = topics.find { it.id == topicId }
    var filter by remember { mutableStateOf("all") }
    var sort by remember { mutableStateOf("number") }
    val base = if (filter == "all") questions else questions.filter { repo.meta(it).difficulty == filter }
    val filtered = when (sort) {
        "difficulty" -> base.sortedBy { difficultyRank(repo.meta(it).difficulty) }
        else -> base
    }
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)) {
        item {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    if (topic != null) {
                        Text(topic.section, style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                        Text(topic.title, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    } else {
                        Text(topicId, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                    }
                }
                var menu by remember { mutableStateOf(false) }
                Box {
                    IconButton(onClick = { menu = true }) {
                        Icon(Icons.Filled.Sort, contentDescription = "Sort")
                    }
                    DropdownMenu(expanded = menu, onDismissRequest = { menu = false }) {
                        listOf("number" to "By number", "difficulty" to "By difficulty").forEach { (k, label) ->
                            DropdownMenuItem(
                                text = { Text(label) },
                                onClick = { sort = k; menu = false },
                                trailingIcon = if (sort == k) {
                                    { Icon(Icons.Filled.Check, null) }
                                } else null,
                            )
                        }
                    }
                }
            }
        }
        item {
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("all", "basic", "intermediate", "advanced").forEach { f ->
                    FilterChip(selected = filter == f, onClick = { filter = f }, label = { Text(f) })
                }
            }
        }
        items(filtered, key = { it.id }) { q ->
            Card(Modifier.fillMaxWidth().clickable { onQuestion(q.id) }) {
                Column(Modifier.padding(14.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("${q.number}", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                        Spacer(Modifier.width(10.dp))
                        Text(q.question, modifier = Modifier.weight(1f), maxLines = 3, overflow = TextOverflow.Ellipsis)
                    }
                    Spacer(Modifier.height(6.dp))
                    MetaLine(q.type, repo.meta(q).difficulty)
                }
            }
        }
    }
}

// ---------------------------------------------------------------- Question (topic page)

@Composable
fun QuestionScreen(repo: Repo, questionId: String) {
    val q by repo.question(questionId).collectAsStateWithLifecycle(null)
    val card by repo.card(questionId).collectAsStateWithLifecycle(null)
    val bookmarks by repo.bookmarkIds().collectAsStateWithLifecycle(emptyList())
    val scope = rememberCoroutineScope()
    val isBookmarked = bookmarks.contains(questionId)

    val item = q ?: return
    val points = remember(item) { repo.points(item) }
    val pitfalls = remember(item) { repo.pitfalls(item) }
    val followups = remember(item) { repo.followups(item) }
    val citations = remember(item) { repo.citations(item) }
    val diagrams = remember(item) { repo.diagrams(item) }
    val techDiagram = remember(item) { repo.diagramTechnical(item) }
    val meta = remember(item) { repo.meta(item) }
    val topics by repo.topics.collectAsStateWithLifecycle(emptyList())
    val topic = topics.find { it.id == item.topicId }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                if (topic != null) {
                    Text(topic.section, style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                    Text(topic.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                } else {
                    Text(item.topicId, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                }
            }
            IconButton(onClick = { scope.launch { repo.toggleBookmark(questionId, isBookmarked) } }) {
                Icon(if (isBookmarked) Icons.Filled.Bookmark else Icons.Outlined.BookmarkBorder, "Bookmark")
            }
        }
        Spacer(Modifier.height(6.dp))
        Text("${item.number}. ${item.question}",
            style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold)
        Spacer(Modifier.height(6.dp))
        MetaLine(item.type, meta.difficulty)
        if (item.tldr.isNotBlank()) {
            Spacer(Modifier.height(8.dp))
            Text("TL;DR", style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
            Spacer(Modifier.height(2.dp))
            Text(item.tldr, style = MaterialTheme.typography.bodyMedium)
        }
        Spacer(Modifier.height(12.dp))
        PointsList(points)
        Section("Concept", item.explain)
        diagrams.forEach { d ->
            Spacer(Modifier.height(8.dp))
            DiagramView(d, citations)
        }
        val plainJ = item.jiuwenPlain
        Section("In Jiuwen", plainJ.ifBlank { item.mechanism })
        TechnicalDetail(if (plainJ.isBlank()) "" else item.mechanism, citations, techDiagram, repo.provenance(item).sources)
        BulletList("Pitfalls", pitfalls)
        BulletList("Likely follow-ups", followups)
        Spacer(Modifier.height(12.dp))
        LinearProgressIndicator(progress = { ((card?.state ?: 0).coerceIn(0, 3)) / 3f },
            modifier = Modifier.fillMaxWidth())
    }
}

// ---------------------------------------------------------------- Progress

@Composable
fun ProgressScreen(repo: Repo) {
    val learned by repo.learnedCount().collectAsStateWithLifecycle(0)
    val new by repo.newCount().collectAsStateWithLifecycle(0)
    val total by repo.totalReviews().collectAsStateWithLifecycle(0)
    val days by repo.activeDays().collectAsStateWithLifecycle(0)
    val mastery by repo.mastery().collectAsStateWithLifecycle(0.0)
    val all = learned + new

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("Progress", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        Card(Modifier.fillMaxWidth()) {
            Row(Modifier.padding(20.dp), verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(110.dp), contentAlignment = Alignment.Center) {
                    ProgressRing((mastery ?: 0.0).toFloat())
                    Text("${((mastery ?: 0.0) * 100).toInt()}%", fontWeight = FontWeight.Bold)
                }
                Spacer(Modifier.width(20.dp))
                Column {
                    Text("Mastery", style = MaterialTheme.typography.titleMedium)
                    Text("$learned of $all questions learned",
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            StatCard("Reviews", "$total", Modifier.weight(1f))
            StatCard("Active days", "$days", Modifier.weight(1f))
        }
    }
}

// ---------------------------------------------------------------- Search

@Composable
fun SearchScreen(repo: Repo, onQuestion: (String) -> Unit) {
    var query by remember { mutableStateOf("") }
    val flow = remember(query) {
        if (query.length >= 2) repo.search(query) else kotlinx.coroutines.flow.flowOf(emptyList())
    }
    val list by flow.collectAsStateWithLifecycle(emptyList())

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        OutlinedTextField(
            value = query, onValueChange = { query = it },
            modifier = Modifier.fillMaxWidth(),
            placeholder = { Text("Search questions, answers, points…") },
            singleLine = true,
        )
        Spacer(Modifier.height(10.dp))
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(list, key = { it.id }) { q ->
                Card(Modifier.fillMaxWidth().clickable { onQuestion(q.id) }) {
                    Column(Modifier.padding(14.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(q.topicId, style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.primary)
                            Spacer(Modifier.width(8.dp))
                            TypeBadge(q.type)
                        }
                        Text(q.question, maxLines = 2, overflow = TextOverflow.Ellipsis)
                    }
                }
            }
        }
    }
}
