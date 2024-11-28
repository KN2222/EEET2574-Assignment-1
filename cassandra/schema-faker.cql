USE kafkapipeline;

CREATE TABLE IF NOT EXISTS kafkapipeline.fakerdata (
  name TEXT,
  address TEXT,
  year INT,
  email TEXT,
  phone_number TEXT,
  company TEXT,
  job TEXT,
  city TEXT,
  country TEXT,
  date_of_birth TEXT,
  PRIMARY KEY (name, address)
);
