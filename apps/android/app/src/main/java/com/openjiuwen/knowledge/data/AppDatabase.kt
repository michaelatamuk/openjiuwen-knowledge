package com.openjiuwen.knowledge.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [
        TopicEntity::class,
        QuestionEntity::class,
        CardEntity::class,
        NoteEntity::class,
        BookmarkEntity::class,
        ReviewLogEntity::class,
    ],
    version = 14,
    exportSchema = false,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun topics(): TopicDao
    abstract fun questions(): QuestionDao
    abstract fun cards(): CardDao
    abstract fun notes(): NoteDao
    abstract fun bookmarks(): BookmarkDao
    abstract fun reviewLog(): ReviewLogDao

    companion object {
        fun build(context: Context): AppDatabase =
            Room.databaseBuilder(context, AppDatabase::class.java, "jiuwen-knowledge.db")
                .fallbackToDestructiveMigration()
                .build()
    }
}
