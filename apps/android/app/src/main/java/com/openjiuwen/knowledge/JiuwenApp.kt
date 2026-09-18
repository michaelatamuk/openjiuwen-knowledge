package com.openjiuwen.knowledge

import android.app.Application
import com.openjiuwen.knowledge.data.AppContainer
import com.openjiuwen.knowledge.data.ContentImporter
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
