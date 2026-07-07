from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import random

from faker import Faker
import pymysql

from app.config import Settings


TABLE_ORDER = [
    "customers",
    "contacts",
    "suppliers",
    "product_categories",
    "products",
    "warehouses",
    "inventory",
    "sales_opportunities",
    "sales_orders",
    "sales_order_items",
    "purchase_orders",
    "purchase_order_items",
]


@dataclass(slots=True)
class ProductRecord:
    id: int
    product_code: str
    sales_price: Decimal
    standard_price: Decimal


class SeedLoader:
    def __init__(self, settings: Settings, locale: str = "zh_CN", seed: int = 20260707) -> None:
        self.settings = settings
        self.fake = Faker(locale)
        Faker.seed(seed)
        random.seed(seed)

    def run(self) -> None:
        with pymysql.connect(**self.settings.mysql_connection_kwargs()) as connection:
            try:
                with connection.cursor() as cursor:
                    self._clear_tables(cursor)
                    customers = self._insert_customers(cursor, count=10)
                    contacts = self._insert_contacts(cursor, customers)
                    suppliers = self._insert_suppliers(cursor, count=10)
                    categories = self._insert_categories(cursor)
                    products = self._insert_products(cursor, suppliers, categories, count=15)
                    warehouses = self._insert_warehouses(cursor, count=10)
                    self._insert_inventory(cursor, products, warehouses)
                    opportunities = self._insert_opportunities(cursor, customers, contacts, count=12)
                    self._insert_sales_orders(cursor, customers, contacts, opportunities, products, count=10)
                    self._insert_purchase_orders(cursor, suppliers, warehouses, products, count=10)
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def _clear_tables(self, cursor: pymysql.cursors.Cursor) -> None:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table_name in reversed(TABLE_ORDER):
            cursor.execute(f"TRUNCATE TABLE `{table_name}`")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    def _insert_customers(self, cursor: pymysql.cursors.Cursor, count: int) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for index in range(1, count + 1):
            customer_code = f"CUST{index:04d}"
            customer_name = f"{self.fake.company()}客户"
            customer_id = self._insert_one(
                cursor,
                """
                INSERT INTO customers
                (customer_code, customer_name, customer_type, industry, phone, email, billing_address, shipping_address, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    customer_code,
                    customer_name,
                    random.choice(["enterprise", "individual"]),
                    random.choice(["制造业", "零售", "教育", "医疗", "软件服务"]),
                    self.fake.phone_number()[:32],
                    f"customer{index}@example.com",
                    self.fake.address()[:255],
                    self.fake.address()[:255],
                    random.choice(["prospect", "active"]),
                ),
            )
            records.append({"id": customer_id, "name": customer_name})
        return records

    def _insert_contacts(
        self, cursor: pymysql.cursors.Cursor, customers: list[dict[str, object]]
    ) -> dict[int, list[dict[str, object]]]:
        records: dict[int, list[dict[str, object]]] = defaultdict(list)
        for customer in customers:
            for contact_index in range(2):
                contact_id = self._insert_one(
                    cursor,
                    """
                    INSERT INTO contacts
                    (customer_id, full_name, job_title, phone, email, is_primary, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        customer["id"],
                        self.fake.name(),
                        random.choice(["采购经理", "销售总监", "财务经理", "IT 主管"]),
                        self.fake.phone_number()[:32],
                        self.fake.email(),
                        1 if contact_index == 0 else 0,
                        "active",
                    ),
                )
                records[int(customer["id"])].append({"id": contact_id})
        return records

    def _insert_suppliers(self, cursor: pymysql.cursors.Cursor, count: int) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for index in range(1, count + 1):
            supplier_id = self._insert_one(
                cursor,
                """
                INSERT INTO suppliers
                (supplier_code, supplier_name, contact_name, phone, email, address, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    f"SUP{index:04d}",
                    f"{self.fake.company()}供应商",
                    self.fake.name(),
                    self.fake.phone_number()[:32],
                    f"supplier{index}@example.com",
                    self.fake.address()[:255],
                    random.choice(["active", "inactive"]),
                ),
            )
            records.append({"id": supplier_id})
        return records

    def _insert_categories(self, cursor: pymysql.cursors.Cursor) -> list[dict[str, object]]:
        category_names = [
            "办公设备",
            "工业零件",
            "电子配件",
            "软件授权",
            "网络设备",
            "包装材料",
            "安全用品",
            "实验器材",
            "物流设备",
            "服务项目",
        ]
        records: list[dict[str, object]] = []
        for index, name in enumerate(category_names, start=1):
            category_id = self._insert_one(
                cursor,
                """
                INSERT INTO product_categories
                (category_code, category_name, description)
                VALUES (%s, %s, %s)
                """,
                (f"CAT{index:04d}", name, f"{name}分类"),
            )
            records.append({"id": category_id, "name": name})
        return records

    def _insert_products(
        self,
        cursor: pymysql.cursors.Cursor,
        suppliers: list[dict[str, object]],
        categories: list[dict[str, object]],
        count: int,
    ) -> list[ProductRecord]:
        records: list[ProductRecord] = []
        for index in range(1, count + 1):
            supplier = random.choice(suppliers)
            category = random.choice(categories)
            standard_price = _money(random.uniform(80, 800))
            sales_price = _money(float(standard_price) * random.uniform(1.1, 1.6))
            product_id = self._insert_one(
                cursor,
                """
                INSERT INTO products
                (product_code, product_name, category_id, supplier_id, unit, standard_price, sales_price, sku, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    f"PROD{index:04d}",
                    f"{category['name']}{index}",
                    category["id"],
                    supplier["id"],
                    random.choice(["pcs", "box", "set", "kg", "meter"]),
                    standard_price,
                    sales_price,
                    f"SKU-{index:05d}",
                    "active",
                ),
            )
            records.append(
                ProductRecord(
                    id=product_id,
                    product_code=f"PROD{index:04d}",
                    sales_price=sales_price,
                    standard_price=standard_price,
                )
            )
        return records

    def _insert_warehouses(self, cursor: pymysql.cursors.Cursor, count: int) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for index in range(1, count + 1):
            warehouse_id = self._insert_one(
                cursor,
                """
                INSERT INTO warehouses
                (warehouse_code, warehouse_name, location, manager_name, status)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    f"WH{index:04d}",
                    f"{random.choice(['华北', '华东', '华南', '西南', '华中'])}仓{index}",
                    self.fake.city(),
                    self.fake.name(),
                    "active",
                ),
            )
            records.append({"id": warehouse_id})
        return records

    def _insert_inventory(
        self,
        cursor: pymysql.cursors.Cursor,
        products: list[ProductRecord],
        warehouses: list[dict[str, object]],
    ) -> None:
        used_pairs: set[tuple[int, int]] = set()
        for product in products:
            selected_warehouses = random.sample(warehouses, k=min(2, len(warehouses)))
            for warehouse in selected_warehouses:
                pair = (product.id, int(warehouse["id"]))
                if pair in used_pairs:
                    continue
                used_pairs.add(pair)
                self._insert_one(
                    cursor,
                    """
                    INSERT INTO inventory
                    (product_id, warehouse_id, quantity_on_hand, quantity_reserved, reorder_level, last_stocked_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        product.id,
                        warehouse["id"],
                        random.randint(50, 300),
                        random.randint(0, 40),
                        random.randint(10, 80),
                    ),
                )

    def _insert_opportunities(
        self,
        cursor: pymysql.cursors.Cursor,
        customers: list[dict[str, object]],
        contacts: dict[int, list[dict[str, object]]],
        count: int,
    ) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for index in range(1, count + 1):
            customer = customers[(index - 1) % len(customers)]
            contact = random.choice(contacts[int(customer["id"])])
            opportunity_id = self._insert_one(
                cursor,
                """
                INSERT INTO sales_opportunities
                (opportunity_code, customer_id, contact_id, title, stage, estimated_amount, expected_close_date, probability, owner_name, notes)
                VALUES (%s, %s, %s, %s, %s, %s, DATE_ADD(CURDATE(), INTERVAL %s DAY), %s, %s, %s)
                """,
                (
                    f"OPP{index:04d}",
                    customer["id"],
                    contact["id"],
                    f"{customer['name']}采购机会{index}",
                    random.choice(["lead", "qualified", "proposal", "negotiation"]),
                    _money(random.uniform(5000, 50000)),
                    random.randint(7, 60),
                    random.choice([20, 40, 60, 80]),
                    self.fake.name(),
                    "由种子脚本自动生成的 CRM 商机记录",
                ),
            )
            records.append({"id": opportunity_id, "customer_id": customer["id"], "contact_id": contact["id"]})
        return records

    def _insert_sales_orders(
        self,
        cursor: pymysql.cursors.Cursor,
        customers: list[dict[str, object]],
        contacts: dict[int, list[dict[str, object]]],
        opportunities: list[dict[str, object]],
        products: list[ProductRecord],
        count: int,
    ) -> None:
        for index in range(1, count + 1):
            customer = customers[(index - 1) % len(customers)]
            contact = random.choice(contacts[int(customer["id"])])
            opportunity = opportunities[(index - 1) % len(opportunities)]
            item_plans = []
            total_amount = Decimal("0.00")
            for product in random.sample(products, k=2):
                quantity = random.randint(1, 6)
                discount_rate = Decimal(str(random.choice([0, 5, 10])))
                line_amount = _money(
                    float(product.sales_price)
                    * quantity
                    * float((Decimal("100") - discount_rate) / Decimal("100"))
                )
                item_plans.append(
                    {
                        "product_id": product.id,
                        "quantity": quantity,
                        "unit_price": product.sales_price,
                        "discount_rate": discount_rate,
                        "line_amount": line_amount,
                    }
                )
                total_amount += line_amount

            sales_order_id = self._insert_one(
                cursor,
                """
                INSERT INTO sales_orders
                (order_no, customer_id, contact_id, opportunity_id, order_status, order_date, currency_code, total_amount, payment_status, shipping_address)
                VALUES (%s, %s, %s, %s, %s, CURDATE(), %s, %s, %s, %s)
                """,
                (
                    f"SO{index:04d}",
                    customer["id"],
                    contact["id"],
                    opportunity["id"],
                    random.choice(["draft", "confirmed", "fulfilled"]),
                    "CNY",
                    _money(float(total_amount)),
                    random.choice(["unpaid", "partial", "paid"]),
                    self.fake.address()[:255],
                ),
            )

            for item in item_plans:
                self._insert_one(
                    cursor,
                    """
                    INSERT INTO sales_order_items
                    (sales_order_id, product_id, quantity, unit_price, discount_rate, line_amount)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        sales_order_id,
                        item["product_id"],
                        item["quantity"],
                        item["unit_price"],
                        item["discount_rate"],
                        item["line_amount"],
                    ),
                )

    def _insert_purchase_orders(
        self,
        cursor: pymysql.cursors.Cursor,
        suppliers: list[dict[str, object]],
        warehouses: list[dict[str, object]],
        products: list[ProductRecord],
        count: int,
    ) -> None:
        for index in range(1, count + 1):
            supplier = suppliers[(index - 1) % len(suppliers)]
            warehouse = warehouses[(index - 1) % len(warehouses)]
            item_plans = []
            total_amount = Decimal("0.00")
            for product in random.sample(products, k=2):
                quantity = random.randint(5, 30)
                line_amount = _money(float(product.standard_price) * quantity)
                item_plans.append(
                    {
                        "product_id": product.id,
                        "quantity": quantity,
                        "unit_cost": product.standard_price,
                        "line_amount": line_amount,
                    }
                )
                total_amount += line_amount

            purchase_order_id = self._insert_one(
                cursor,
                """
                INSERT INTO purchase_orders
                (po_no, supplier_id, warehouse_id, po_status, order_date, expected_arrival_date, total_amount, buyer_name)
                VALUES (%s, %s, %s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL %s DAY), %s, %s)
                """,
                (
                    f"PO{index:04d}",
                    supplier["id"],
                    warehouse["id"],
                    random.choice(["draft", "ordered", "received"]),
                    random.randint(3, 21),
                    _money(float(total_amount)),
                    self.fake.name(),
                ),
            )

            for item in item_plans:
                self._insert_one(
                    cursor,
                    """
                    INSERT INTO purchase_order_items
                    (purchase_order_id, product_id, quantity, unit_cost, line_amount)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        purchase_order_id,
                        item["product_id"],
                        item["quantity"],
                        item["unit_cost"],
                        item["line_amount"],
                    ),
                )

    @staticmethod
    def _insert_one(
        cursor: pymysql.cursors.Cursor, sql: str, params: tuple[object, ...]
    ) -> int:
        cursor.execute(sql, params)
        return int(cursor.lastrowid)


def _money(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def main() -> None:
    settings = Settings.from_env()
    SeedLoader(settings).run()
    print("Seed data inserted successfully.")


if __name__ == "__main__":
    main()
