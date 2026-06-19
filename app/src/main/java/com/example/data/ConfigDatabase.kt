package com.example.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(entities = [ConfigHistory::class], version = 1, exportSchema = false)
abstract class ConfigDatabase : RoomDatabase() {
    abstract fun configHistoryDao(): ConfigHistoryDao

    companion object {
        @Volatile
        private var INSTANCE: ConfigDatabase? = null

        fun getDatabase(context: Context): ConfigDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    ConfigDatabase::class.java,
                    "config_database"
                )
                .fallbackToDestructiveMigration()
                .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
