package com.jiuwenswarm.study.data

import android.content.Context

class AppContainer(context: Context) {
    val db: AppDatabase = AppDatabase.build(context)
    val repo: Repo = Repo(db)
}
