package com.jiuwenswarm.study

import android.app.Application
import com.jiuwenswarm.study.data.AppContainer
import com.jiuwenswarm.study.data.ContentImporter
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class JiuwenApp : Application() {

    lateinit var container: AppContainer
        private set

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
        scope.launch { ContentImporter.importIfNeeded(this@JiuwenApp, container.db) }
    }
}
