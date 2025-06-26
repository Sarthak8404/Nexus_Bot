-- Create extracted_data table
CREATE TABLE extracted_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    content_type TEXT NOT NULL,
    source TEXT NOT NULL,
    data JSONB NOT NULL,
    filename TEXT,
    url TEXT,
    stats JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for better query performance
CREATE INDEX idx_extracted_data_user_id ON extracted_data(user_id);

-- Enable RLS
ALTER TABLE extracted_data ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (temporary for development)
CREATE POLICY "Allow all operations on extracted_data"
    ON extracted_data FOR ALL
    USING (true)
    WITH CHECK (true); 