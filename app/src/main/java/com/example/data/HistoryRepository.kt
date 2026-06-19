package com.example.data

import kotlinx.coroutines.flow.Flow

class HistoryRepository(private val dao: ConfigHistoryDao) {
    val allHistory: Flow<List<ConfigHistory>> = dao.getAllHistory()

    suspend fun insertHistory(history: ConfigHistory) {
        dao.insertHistory(history)
    }

    suspend fun deleteHistoryById(id: Int) {
        dao.deleteHistoryById(id)
    }

    suspend fun clearHistory() {
        dao.clearAllHistory()
    }
}
