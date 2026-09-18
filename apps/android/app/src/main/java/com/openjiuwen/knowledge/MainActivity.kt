package com.openjiuwen.knowledge

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.openjiuwen.knowledge.ui.AppNav
import com.openjiuwen.knowledge.ui.theme.JiuwenTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val repo = (application as JiuwenApp).container.repo
        setContent {
            JiuwenTheme {
                AppNav(repo)
            }
        }
    }
}
