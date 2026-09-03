ALTER TABLE users
    ADD COLUMN role ENUM('user', 'admin') NOT NULL DEFAULT 'user'
    AFTER password;

-- Existing rows receive the column default and remain regular users.

ALTER TABLE chat_messages
    DROP FOREIGN KEY chat_messages_ibfk_1,
    DROP FOREIGN KEY chat_messages_ibfk_2;

ALTER TABLE chat_messages
    ADD CONSTRAINT chat_messages_ibfk_1
        FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
        ON DELETE CASCADE,
    ADD CONSTRAINT chat_messages_ibfk_2
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE;

ALTER TABLE chat_sessions
    DROP FOREIGN KEY chat_sessions_ibfk_1;

ALTER TABLE chat_sessions
    ADD CONSTRAINT chat_sessions_ibfk_1
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE;

ALTER TABLE documents
    DROP FOREIGN KEY documents_ibfk_1;

ALTER TABLE documents
    ADD CONSTRAINT documents_ibfk_1
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE;
