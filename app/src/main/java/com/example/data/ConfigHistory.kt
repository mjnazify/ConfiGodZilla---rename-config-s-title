package com.example.data

import androidx.room.Dao
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "config_history")
data class ConfigHistory(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val inputSummary: String,
    val configCount: Int,
    val outputMode: String,
    val outputLinkOrPath: String,
    val rawConfigs: String,
    val processedConfigs: String,
    val timestamp: Long = System.currentTimeMillis()
)

@Dao
interface ConfigHistoryDao {
    @Query("SELECT * FROM config_history ORDER BY timestamp DESC")
    fun getAllHistory(): Flow<List<ConfigHistory>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertHistory(history: ConfigHistory)

    @Query("DELETE FROM config_history WHERE id = :id")
    suspend fun deleteHistoryById(id: Int)

    @Query("DELETE FROM config_history")
    suspend fun clearAllHistory()
}
