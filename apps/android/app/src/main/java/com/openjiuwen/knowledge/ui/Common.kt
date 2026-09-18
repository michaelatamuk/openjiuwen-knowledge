package com.openjiuwen.knowledge.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.rememberTransformableState
import androidx.compose.foundation.gestures.transformable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ChevronLeft
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.ContentCopy
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import coil.ImageLoader
import coil.compose.AsyncImage
import coil.decode.SvgDecoder
import com.openjiuwen.knowledge.data.CitationDto
import com.openjiuwen.knowledge.data.DiagramData
import com.openjiuwen.knowledge.data.DiagramNodeDto
import kotlinx.coroutines.delay

/** Minimal, dependency-free markdown renderer: **bold** and `code` spans. */
fun renderMarkdown(text: String): AnnotatedString {
    val regex = Regex("\\*\\*.+?\\*\\*|`[^`]+`", RegexOption.DOT_MATCHES_ALL)
    return buildAnnotatedString {
        var last = 0
        for (m in regex.findAll(text)) {
            append(text.substring(last, m.range.first))
            val tok = m.value
            if (tok.startsWith("**")) {
                withStyle(SpanStyle(fontWeight = FontWeight.Bold)) { append(tok.substring(2, tok.length - 2)) }
            } else {
                withStyle(SpanStyle(fontFamily = FontFamily.Monospace, background = Color(0x22607090))) {
                    append(tok.substring(1, tok.length - 1))
                }
            }
            last = m.range.last + 1
        }
        append(text.substring(last))
    }
}

@Composable
fun MarkdownText(text: String, modifier: Modifier = Modifier) {
    Text(text = remember(text) { renderMarkdown(text) },
        style = MaterialTheme.typography.bodyLarge, modifier = modifier)
}

@Composable
fun TypeBadge(type: String) {
    val color = when (type) {
        "compare" -> MaterialTheme.colorScheme.tertiary
        "design" -> MaterialTheme.colorScheme.secondary
        "mechanism" -> MaterialTheme.colorScheme.primary
        "behavioral" -> MaterialTheme.colorScheme.error
        else -> MaterialTheme.colorScheme.outline
    }
    Box(
        Modifier.background(color.copy(alpha = 0.12f), RoundedCornerShape(999.dp))
            .padding(horizontal = 10.dp, vertical = 2.dp),
    ) {
        Text(type.replaceFirstChar { it.uppercase() }, style = MaterialTheme.typography.labelSmall, color = color)
    }
}

@Composable
fun ProgressRing(
    progress: Float,
    modifier: Modifier = Modifier,
    color: Color = MaterialTheme.colorScheme.primary,
    track: Color = MaterialTheme.colorScheme.surfaceVariant,
) {
    Canvas(modifier = modifier) {
        val stroke = size.minDimension * 0.12f
        drawArc(color = track, startAngle = -90f, sweepAngle = 360f, useCenter = false,
            style = Stroke(width = stroke, cap = StrokeCap.Round))
        drawArc(color = color, startAngle = -90f, sweepAngle = 360f * progress.coerceIn(0f, 1f),
            useCenter = false, style = Stroke(width = stroke, cap = StrokeCap.Round))
    }
}

// --------------------------------------------------------------------- answer layers

@Composable
fun PointsList(points: List<String>) {
    if (points.isEmpty()) return
    val checked = remember(points) { mutableStateListOf<Boolean>().apply { repeat(points.size) { add(false) } } }
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        points.forEachIndexed { i, p ->
            Row(Modifier.fillMaxWidth().clickable { checked[i] = !checked[i] }, verticalAlignment = Alignment.Top) {
                Text(if (checked[i]) "✓" else "${i + 1}", fontWeight = FontWeight.Bold,
                    color = if (checked[i]) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outline,
                    modifier = Modifier.width(24.dp))
                Text(p, style = MaterialTheme.typography.bodyLarge)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun CitationChips(citations: List<CitationDto>) {
    if (citations.isEmpty()) return
    var selected by remember { mutableStateOf<CitationDto?>(null) }
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        citations.forEach { c ->
            AssistChip(
                onClick = { selected = c },
                label = { Text(c.symbol.ifBlank { c.ref.substringAfterLast('/') }, maxLines = 1) },
                leadingIcon = { Icon(Icons.Filled.ContentCopy, null, Modifier.size(AssistChipDefaults.IconSize)) },
            )
        }
    }
    selected?.let { c ->
        ModalBottomSheet(onDismissRequest = { selected = null }, sheetState = rememberModalBottomSheetState()) {
            val clip = LocalClipboardManager.current
            Column(Modifier.fillMaxWidth().padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                TypeBadge(c.kind)
                Text(c.symbol.ifBlank { "Code reference" }, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Text(c.ref, style = MaterialTheme.typography.bodyMedium, fontFamily = FontFamily.Monospace)
                if (c.desc.isNotBlank()) Text(c.desc, style = MaterialTheme.typography.bodyMedium)
                if (c.lines.isNotBlank()) Text("lines ${c.lines}", style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
                Row(horizontalArrangement = Arrangement.End, modifier = Modifier.fillMaxWidth()) {
                    TextButton(onClick = { clip.setText(AnnotatedString("${c.ref}\n${c.desc}")); selected = null }) { Text("Copy") }
                }
                Spacer(Modifier.height(8.dp))
            }
        }
    }
}

// --------------------------------------------------------------------- diagram

private fun svgLoader(context: android.content.Context): ImageLoader =
    ImageLoader.Builder(context).components { add(SvgDecoder.Factory()) }.build()

@Composable
private fun SvgZoomDialog(asset: String, loader: ImageLoader, onClose: () -> Unit) {
    var scale by remember { mutableFloatStateOf(1f) }
    var offset by remember { mutableStateOf(Offset.Zero) }
    val state = rememberTransformableState { z, pan, _ ->
        val ns = (scale * z).coerceIn(1f, 12f); scale = ns
        offset = if (ns <= 1f) Offset.Zero else offset + pan
    }
    Dialog(onDismissRequest = onClose, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Box(Modifier.fillMaxSize().background(Color(0xF0000000))) {
            AsyncImage(
                model = "file:///android_asset/$asset", imageLoader = loader, contentDescription = "diagram",
                contentScale = ContentScale.Fit,
                modifier = Modifier.fillMaxSize().pointerInput(Unit) {
                    detectTapGestures(onDoubleTap = { if (scale > 1f) { scale = 1f; offset = Offset.Zero } else scale = 3f })
                }.graphicsLayer {
                    scaleX = scale; scaleY = scale; translationX = offset.x; translationY = offset.y
                }.transformable(state),
            )
            IconButton(onClick = onClose, modifier = Modifier.align(Alignment.TopEnd).padding(12.dp)) {
                Icon(Icons.Filled.Close, "Close", tint = Color.White)
            }
            Text("Pinch to zoom · drag to pan · double-tap", color = Color.White,
                style = MaterialTheme.typography.labelSmall,
                modifier = Modifier.align(Alignment.BottomCenter).padding(16.dp))
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DiagramView(data: DiagramData, citations: List<CitationDto>) {
    val context = LocalContext.current
    val haptic = LocalHapticFeedback.current
    val loader = remember(context) { svgLoader(context) }
    // Display PNG (Mermaid SVG is not rendered correctly by AndroidSVG).
    var useSvg by remember(data) { mutableStateOf(false) }
    val asset = when {
        !useSvg && data.image.isNotBlank() -> data.image
        data.svgDark.isNotBlank() && isSystemInDarkTheme() -> data.svgDark
        data.svg.isNotBlank() -> data.svg
        else -> data.image
    }
    val darkSurface = false

    var full by remember { mutableStateOf(false) }
    var step by remember { mutableIntStateOf(-1) }
    var playing by remember { mutableStateOf(false) }
    var selected by remember { mutableStateOf<DiagramNodeDto?>(null) }

    val currentLabel = if (step in data.steps.indices) data.steps[step] else null
    LaunchedEffect(playing) {
        if (playing) {
            while (step < data.steps.size - 1) {
                delay(1300); step++; haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
            }
            playing = false
        }
    }

    Column(Modifier.fillMaxWidth()) {
        Box(
            Modifier.fillMaxWidth()
                .background(
                    if (darkSurface) MaterialTheme.colorScheme.surfaceVariant else Color(0xFFFFFFFF),
                    RoundedCornerShape(12.dp),
                )
                .aspectRatio(if (data.h > 0f && data.w > 0f) data.w / data.h else 1.6f)
                .pointerInput(data, step) {
                    detectTapGestures { off ->
                        val sw = if (data.w > 0f) data.w else size.width.toFloat()
                        val sh = if (data.h > 0f) data.h else size.height.toFloat()
                        val sx = size.width / sw; val sy = size.height / sh
                        val hit = data.nodes.minByOrNull { n ->
                            val dx = n.x * sx - off.x; val dy = n.y * sy - off.y; dx * dx + dy * dy
                        }
                        if (hit != null) {
                            val dx = hit.x * sx - off.x; val dy = hit.y * sy - off.y
                            val r = size.width * 0.12f
                            if (dx * dx + dy * dy < r * r) {
                                selected = hit; haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                            }
                        }
                    }
                },
            contentAlignment = Alignment.Center,
        ) {
            AsyncImage(model = "file:///android_asset/$asset", imageLoader = loader,
                contentDescription = data.alt.ifBlank { "diagram" }, contentScale = ContentScale.Fit,
                onError = { useSvg = false },
                modifier = Modifier.fillMaxSize())
            Canvas(Modifier.fillMaxSize()) {
                currentLabel?.let { lbl ->
                    val sw = if (data.w > 0f) data.w else size.width
                    val sh = if (data.h > 0f) data.h else size.height
                    val sx = size.width / sw; val sy = size.height / sh
                    data.nodes.filter { it.label == lbl }.forEach { n ->
                        val c = Offset(n.x * sx, n.y * sy)
                        drawCircle(Color(0x334C5BD4), radius = size.minDimension * 0.1f, center = c)
                        drawCircle(Color(0xFF4C5BD4), radius = size.minDimension * 0.1f, center = c,
                            style = Stroke(width = 5f))
                    }
                }
            }
            TextButton(onClick = { full = true }, modifier = Modifier.align(Alignment.TopEnd)) { Text("Expand") }
        }
        if (data.steps.size >= 2) {
            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
                IconButton(onClick = { if (step > 0) { step--; haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove) } }, enabled = step > 0) {
                    Icon(Icons.Filled.ChevronLeft, "Previous step")
                }
                Column(Modifier.weight(1f)) {
                    Text(if (step >= 0) "Step ${step + 1} / ${data.steps.size}" else "Step through the flow",
                        style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(currentLabel ?: "Tap play", style = MaterialTheme.typography.bodyMedium)
                }
                IconButton(onClick = { if (step < data.steps.size - 1) { step++; haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove) } }, enabled = step < data.steps.size - 1) {
                    Icon(Icons.Filled.ChevronRight, "Next step")
                }
                IconButton(onClick = { if (playing) playing = false else { if (step >= data.steps.size - 1) step = -1; playing = true } }) {
                    Icon(Icons.Filled.PlayArrow, "Play")
                }
            }
        }
    }

    if (full) SvgZoomDialog(asset, loader) { full = false }

    selected?.let { node ->
        ModalBottomSheet(onDismissRequest = { selected = null }, sheetState = rememberModalBottomSheetState()) {
            Column(Modifier.fillMaxWidth().padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(node.label, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                val match = citations.firstOrNull {
                    it.symbol.isNotBlank() && (it.symbol.equals(node.label, true) ||
                        it.desc.contains(node.label, true) || node.label.contains(it.symbol, true))
                }
                if (match != null) {
                    Text(match.ref, style = MaterialTheme.typography.bodyMedium, fontFamily = FontFamily.Monospace)
                    if (match.desc.isNotBlank()) Text(match.desc, style = MaterialTheme.typography.bodyMedium)
                } else {
                    Text("Part of the flow above.", style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                Spacer(Modifier.height(8.dp))
            }
        }
    }
}

@Composable
private fun TechTitle(title: String) {
    Text(title, style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.Bold,
        color = MaterialTheme.colorScheme.primary, modifier = Modifier.padding(top = 10.dp, bottom = 2.dp))
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun TechnicalDetail(
    text: String,
    citations: List<CitationDto>,
    diagram: DiagramData? = null,
    sources: List<String> = emptyList(),
) {
    if (text.isBlank() && citations.isEmpty() && diagram == null && sources.isEmpty()) return
    var open by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxWidth()) {
        TextButton(onClick = { open = !open }) {
            Text(if (open) "Hide Jiuwen technical detail" else "Jiuwen technical detail (classes & functions)")
        }
        if (open) {
            if (text.isNotBlank()) {
                TechTitle("Implementation")
                MarkdownText(text)
            }
            if (citations.isNotEmpty()) {
                TechTitle("Code anchors")
                CitationChips(citations)
            }
            if (diagram != null) {
                TechTitle("Implementation diagram")
                DiagramView(diagram, citations)
            }
            if (sources.isNotEmpty()) {
                TechTitle("Canonical source")
                Text(sources.joinToString(", "), style = MaterialTheme.typography.labelSmall,
                    fontFamily = FontFamily.Monospace)
            }
        }
    }
}

@Composable
fun RatingBar(onRate: (Int) -> Unit) {
    val labels = listOf("Again", "Hard", "Good", "Easy")
    val colors = listOf(Color(0xFFE5484D), Color(0xFFF5A524), Color(0xFF30A46C), Color(0xFF3E63DD))
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        labels.forEachIndexed { i, label ->
            Button(
                onClick = { onRate(i + 1) }, modifier = Modifier.weight(1f),
                colors = ButtonDefaults.buttonColors(containerColor = colors[i], contentColor = Color.White),
                shape = RoundedCornerShape(12.dp),
                contentPadding = androidx.compose.foundation.layout.PaddingValues(vertical = 12.dp),
            ) { Text(label, maxLines = 1) }
        }
    }
}
