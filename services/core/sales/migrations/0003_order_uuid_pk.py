import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sales", "0002_refactor_order_orderitem_integrationlog"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE sales_order ADD COLUMN new_id UUID DEFAULT gen_random_uuid() NOT NULL;

            ALTER TABLE sales_orderitem ADD COLUMN order_new_id UUID;
            UPDATE sales_orderitem oi
               SET order_new_id = o.new_id
              FROM sales_order o
             WHERE oi.order_id = o.id;

            ALTER TABLE sales_integrationlog ADD COLUMN order_new_id UUID;
            UPDATE sales_integrationlog il
               SET order_new_id = o.new_id
              FROM sales_order o
             WHERE il.order_id = o.id;

            DO $$
            DECLARE cname text;
            BEGIN
                SELECT conname INTO cname FROM pg_constraint
                 WHERE conrelid = 'sales_orderitem'::regclass AND contype = 'f'
                   AND confrelid = 'sales_order'::regclass;
                IF cname IS NOT NULL THEN
                    EXECUTE 'ALTER TABLE sales_orderitem DROP CONSTRAINT ' || quote_ident(cname);
                END IF;
            END $$;

            DO $$
            DECLARE cname text;
            BEGIN
                SELECT conname INTO cname FROM pg_constraint
                 WHERE conrelid = 'sales_integrationlog'::regclass AND contype = 'f'
                   AND confrelid = 'sales_order'::regclass;
                IF cname IS NOT NULL THEN
                    EXECUTE 'ALTER TABLE sales_integrationlog DROP CONSTRAINT ' || quote_ident(cname);
                END IF;
            END $$;

            ALTER TABLE sales_order DROP CONSTRAINT sales_order_pkey;
            ALTER TABLE sales_order DROP COLUMN id;
            ALTER TABLE sales_order RENAME COLUMN new_id TO id;
            ALTER TABLE sales_order ADD PRIMARY KEY (id);

            ALTER TABLE sales_orderitem DROP COLUMN order_id;
            ALTER TABLE sales_orderitem RENAME COLUMN order_new_id TO order_id;
            ALTER TABLE sales_orderitem ALTER COLUMN order_id SET NOT NULL;
            ALTER TABLE sales_orderitem
                ADD CONSTRAINT sales_orderitem_order_id_fk
                FOREIGN KEY (order_id) REFERENCES sales_order(id) ON DELETE CASCADE;

            ALTER TABLE sales_integrationlog DROP COLUMN order_id;
            ALTER TABLE sales_integrationlog RENAME COLUMN order_new_id TO order_id;
            ALTER TABLE sales_integrationlog
                ADD CONSTRAINT sales_integrationlog_order_id_fk
                FOREIGN KEY (order_id) REFERENCES sales_order(id) ON DELETE SET NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="order",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AddField(
                    model_name="orderitem",
                    name="order",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="sales.order",
                    ),
                ),
                migrations.AddField(
                    model_name="integrationlog",
                    name="order",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="logs",
                        to="sales.order",
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
