package com.jiuwenswarm.study

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.jiuwenswarm.study.ui.AppNav
import com.jiuwenswarm.study.ui.theme.JiuwenTheme

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
