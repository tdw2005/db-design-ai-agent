# ERP 数据模型调研

ERP 系统通常围绕采购、库存、产品、订单履约等流程建模，核心关注物料主数据、库存余额、采购单据和销售单据之间的联动关系。

## ER 图

```mermaid
erDiagram
    CUSTOMER ||--o{ SALES_ORDER : places
    SALES_ORDER ||--|{ SALES_ORDER_ITEM : contains
    PRODUCT ||--o{ SALES_ORDER_ITEM : sold_as

    SUPPLIER ||--o{ PRODUCT : supplies
    PRODUCT_CATEGORY ||--o{ PRODUCT : classifies

    PRODUCT ||--o{ INVENTORY : tracked_in
    WAREHOUSE ||--o{ INVENTORY : stores

    SUPPLIER ||--o{ PURCHASE_ORDER : receives
    PURCHASE_ORDER ||--|{ PURCHASE_ORDER_ITEM : contains
    PRODUCT ||--o{ PURCHASE_ORDER_ITEM : purchased_as
    WAREHOUSE ||--o{ PURCHASE_ORDER : delivered_to

    CUSTOMER {
        bigint_unsigned id PK
        varchar customer_code UK
        varchar customer_name
        varchar customer_type
        varchar status
    }
    SUPPLIER {
        bigint_unsigned id PK
        varchar supplier_code UK
        varchar supplier_name
        varchar contact_name
        varchar status
    }
    PRODUCT_CATEGORY {
        bigint_unsigned id PK
        varchar category_code UK
        varchar category_name
    }
    PRODUCT {
        bigint_unsigned id PK
        bigint_unsigned category_id FK
        bigint_unsigned supplier_id FK
        varchar product_code UK
        varchar product_name
        decimal standard_price
        decimal sales_price
        varchar unit
    }
    WAREHOUSE {
        bigint_unsigned id PK
        varchar warehouse_code UK
        varchar warehouse_name
        varchar location
    }
    INVENTORY {
        bigint_unsigned id PK
        bigint_unsigned product_id FK
        bigint_unsigned warehouse_id FK
        int quantity_on_hand
        int reorder_level
    }
    PURCHASE_ORDER {
        bigint_unsigned id PK
        bigint_unsigned supplier_id FK
        bigint_unsigned warehouse_id FK
        varchar po_no UK
        varchar po_status
        date order_date
    }
    PURCHASE_ORDER_ITEM {
        bigint_unsigned id PK
        bigint_unsigned purchase_order_id FK
        bigint_unsigned product_id FK
        int quantity
        decimal unit_cost
        decimal line_amount
    }
    SALES_ORDER {
        bigint_unsigned id PK
        bigint_unsigned customer_id FK
        varchar order_no UK
        varchar order_status
        date order_date
        decimal total_amount
    }
    SALES_ORDER_ITEM {
        bigint_unsigned id PK
        bigint_unsigned sales_order_id FK
        bigint_unsigned product_id FK
        int quantity
        decimal unit_price
        decimal line_amount
    }
```

## 类图视角

从类图抽象角度看，ERP 更强调“主数据类 + 单据类 + 明细类 + 库存类”的协作关系：`Supplier`、`ProductCategory`、`Product`、`Warehouse` 属于主数据；`PurchaseOrder`、`SalesOrder` 属于业务单据；`PurchaseOrderItem`、`SalesOrderItem` 属于明细对象；`Inventory` 负责连接产品与仓库并记录库存状态。

```mermaid
classDiagram
    class Supplier {
        +id: bigint
        +supplier_code: string
        +supplier_name: string
        +status: string
    }
    class ProductCategory {
        +id: bigint
        +category_code: string
        +category_name: string
    }
    class Product {
        +id: bigint
        +product_code: string
        +product_name: string
        +standard_price: decimal
        +sales_price: decimal
        +unit: string
    }
    class Warehouse {
        +id: bigint
        +warehouse_code: string
        +warehouse_name: string
        +location: string
    }
    class Inventory {
        +id: bigint
        +quantity_on_hand: int
        +reorder_level: int
    }
    class PurchaseOrder {
        +id: bigint
        +po_no: string
        +po_status: string
        +order_date: date
    }
    class PurchaseOrderItem {
        +id: bigint
        +quantity: int
        +unit_cost: decimal
        +line_amount: decimal
    }
    class SalesOrder {
        +id: bigint
        +order_no: string
        +order_status: string
        +order_date: date
        +total_amount: decimal
    }
    class SalesOrderItem {
        +id: bigint
        +quantity: int
        +unit_price: decimal
        +line_amount: decimal
    }

    Supplier "1" --> "many" Product : supplies
    ProductCategory "1" --> "many" Product : classifies
    Product "1" --> "many" Inventory : tracked_in
    Warehouse "1" --> "many" Inventory : stores
    Supplier "1" --> "many" PurchaseOrder : receives
    PurchaseOrder "1" --> "many" PurchaseOrderItem : contains
    Product "1" --> "many" PurchaseOrderItem : purchased_as
    SalesOrder "1" --> "many" SalesOrderItem : contains
    Product "1" --> "many" SalesOrderItem : sold_as
```
