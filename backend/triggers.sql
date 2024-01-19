CREATE
OR REPLACE FUNCTION validate_transaction()
RETURNS TRIGGER AS $$
BEGIN
    -- Add your validation logic here
    IF
NEW.amount <= 0 THEN
        RAISE EXCEPTION 'Amount must be greater than zero';
END IF;

    -- You can perform additional checks or actions as needed

RETURN NEW;
END;
$$
LANGUAGE plpgsql;


CREATE TRIGGER transaction_validation_trigger
    BEFORE INSERT OR
UPDATE ON yourapp_transaction
    FOR EACH ROW EXECUTE FUNCTION validate_transaction();


DROP TRIGGER IF EXISTS transaction_validation_trigger ON yourapp_transaction;

