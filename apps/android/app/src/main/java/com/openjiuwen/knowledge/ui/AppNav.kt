package com.openjiuwen.knowledge.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Insights
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.School
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Today
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.openjiuwen.knowledge.data.Repo

private data class Tab(val route: String, val label: String, val icon: ImageVector)

private val TABS = listOf(
    Tab("today", "Today", Icons.Filled.Today),
    Tab("study", "Study", Icons.Filled.School),
    Tab("explore", "Explore", Icons.Filled.MenuBook),
    Tab("progress", "Progress", Icons.Filled.Insights),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppNav(repo: Repo) {
    val nav = rememberNavController()
    val backStack by nav.currentBackStackEntryAsState()
    val route = backStack?.destination?.route
    val chrome = route in setOf("today", "study", "explore", "progress")

    Scaffold(
        topBar = {
            if (chrome) {
                TopAppBar(
                    title = { Text("Jiuwen Study") },
                    actions = {
                        IconButton(onClick = { nav.navigate("search") }) {
                            Icon(Icons.Filled.Search, contentDescription = "Search")
                        }
                    },
                )
            }
        },
        bottomBar = {
            if (chrome) {
                NavigationBar {
                    TABS.forEach { tab ->
                        NavigationBarItem(
                            selected = route == tab.route,
                            onClick = {
                                nav.navigate(tab.route) {
                                    launchSingleTop = true
                                    restoreState = true
                                    popUpTo("today") { saveState = true }
                                }
                            },
                            icon = { Icon(tab.icon, contentDescription = tab.label) },
                            label = { Text(tab.label) },
                        )
                    }
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = nav,
            startDestination = "today",
            modifier = Modifier.padding(padding),
        ) {
            composable("today") {
                TodayScreen(repo, onStudy = { nav.navigate("study") }, onExplore = { nav.navigate("explore") })
            }
            composable("study") { StudyScreen(repo) { id -> nav.navigate("question/$id") } }
            composable("explore") { ExploreScreen(repo) { id -> nav.navigate("topic/$id") } }
            composable("progress") { ProgressScreen(repo) }
            composable("search") { SearchScreen(repo) { id -> nav.navigate("question/$id") } }
            composable("topic/{id}") { entry ->
                TopicScreen(repo, entry.arguments?.getString("id") ?: "") { id ->
                    nav.navigate("question/$id")
                }
            }
            composable("question/{id}") { entry ->
                QuestionScreen(repo, entry.arguments?.getString("id") ?: "")
            }
        }
    }
}
