package com.openjiuwen.knowledge.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

@Dao
interface TopicDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(items: List<TopicEntity>)

    @Query("SELECT * FROM topics ORDER BY orderIndex")
    fun observeAll(): Flow<List<TopicEntity>>

    @Query("SELECT COUNT(*) FROM topics")
    suspend fun count(): Int
}

@Dao
interface QuestionDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(items: List<QuestionEntity>)

    @Query("SELECT * FROM questions WHERE topicId = :topicId ORDER BY number")
    fun observeByTopic(topicId: String): Flow<List<QuestionEntity>>

    @Query("SELECT * FROM questions WHERE id = :id")
    suspend fun byId(id: String): QuestionEntity?

    @Query("SELECT * FROM questions WHERE id = :id")
    fun observeById(id: String): Flow<QuestionEntity?>

    @Query("SELECT COUNT(*) FROM questions")
    suspend fun count(): Int

    @Query("SELECT * FROM questions WHERE searchBlob LIKE '%'||:q||'%' ORDER BY topicId, number LIMIT 60")
    fun search(q: String): Flow<List<QuestionEntity>>
}

@Dao
interface CardDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(items: List<CardEntity>)

    @Update
    suspend fun update(card: CardEntity)

    @Query("SELECT * FROM cards WHERE questionId = :id")
    suspend fun byId(id: String): CardEntity?

    @Query("SELECT * FROM cards WHERE questionId = :id")
    fun observeById(id: String): Flow<CardEntity?>

    @Query("SELECT COUNT(*) FROM cards WHERE due <= :now AND due > 0")
    fun observeDueCount(now: Long): Flow<Int>

    @Query("SELECT COUNT(*) FROM cards WHERE state = 0")
    fun observeNewCount(): Flow<Int>

    @Query("SELECT COUNT(*) FROM cards WHERE state >= 2")
    fun observeLearnedCount(): Flow<Int>

    @Query("SELECT c.* FROM cards c JOIN questions q ON q.id = c.questionId WHERE (c.due <= :now AND c.due > 0) ORDER BY c.due LIMIT :limit")
    suspend fun dueCards(now: Long, limit: Int): List<CardEntity>

    @Query("SELECT c.* FROM cards c WHERE c.state = 0 ORDER BY RANDOM() LIMIT :limit")
    suspend fun newCards(limit: Int): List<CardEntity>

    @Query("SELECT c.* FROM cards c JOIN questions q ON q.id = c.questionId WHERE q.topicId = :topicId")
    suspend fun cardsForTopic(topicId: String): List<CardEntity>

    @Query("SELECT AVG(CASE WHEN state >= 2 THEN 1.0 ELSE 0.0 END) FROM cards")
    fun observeMastery(): Flow<Double?>
}

@Dao
interface NoteDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(note: NoteEntity)

    @Query("SELECT * FROM notes WHERE questionId = :id")
    fun observe(id: String): Flow<NoteEntity?>

    @Query("DELETE FROM notes WHERE questionId = :id")
    suspend fun delete(id: String)
}

@Dao
interface BookmarkDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun add(b: BookmarkEntity)

    @Query("DELETE FROM bookmarks WHERE questionId = :id")
    suspend fun remove(id: String)

    @Query("SELECT questionId FROM bookmarks")
    fun observeIds(): Flow<List<String>>
}

@Dao
interface ReviewLogDao {
    @Insert
    suspend fun insert(log: ReviewLogEntity)

    @Query("SELECT COUNT(*) FROM review_log WHERE reviewedAt >= :since")
    fun observeReviewsSince(since: Long): Flow<Int>

    @Query("SELECT COUNT(*) FROM review_log")
    fun observeTotalReviews(): Flow<Int>

    @Query("SELECT COUNT(DISTINCT date(reviewedAt/1000,'unixepoch','localtime')) FROM review_log")
    fun observeActiveDays(): Flow<Int>
}
