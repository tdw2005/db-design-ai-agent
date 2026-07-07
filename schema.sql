CREATE TABLE IF NOT EXISTS customers (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    customer_code VARCHAR(32) NOT NULL,
    customer_name VARCHAR(128) NOT NULL,
    customer_type ENUM('enterprise', 'individual') NOT NULL DEFAULT 'enterprise',
    industry VARCHAR(64) DEFAULT NULL,
    phone VARCHAR(32) DEFAULT NULL,
    email VARCHAR(128) DEFAULT NULL,
    billing_address VARCHAR(255) DEFAULT NULL,
    shipping_address VARCHAR(255) DEFAULT NULL,
    status ENUM('prospect', 'active', 'inactive') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_customers_customer_code (customer_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS contacts (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    customer_id BIGINT UNSIGNED NOT NULL,
    full_name VARCHAR(128) NOT NULL,
    job_title VARCHAR(64) DEFAULT NULL,
    phone VARCHAR(32) DEFAULT NULL,
    email VARCHAR(128) DEFAULT NULL,
    is_primary TINYINT(1) NOT NULL DEFAULT 0,
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_contacts_customer_id (customer_id),
    CONSTRAINT fk_contacts_customer_id FOREIGN KEY (customer_id) REFERENCES customers (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS suppliers (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    supplier_code VARCHAR(32) NOT NULL,
    supplier_name VARCHAR(128) NOT NULL,
    contact_name VARCHAR(64) DEFAULT NULL,
    phone VARCHAR(32) DEFAULT NULL,
    email VARCHAR(128) DEFAULT NULL,
    address VARCHAR(255) DEFAULT NULL,
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_suppliers_supplier_code (supplier_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS product_categories (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    category_code VARCHAR(32) NOT NULL,
    category_name VARCHAR(128) NOT NULL,
    description TEXT DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_product_categories_category_code (category_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS products (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    product_code VARCHAR(32) NOT NULL,
    product_name VARCHAR(128) NOT NULL,
    category_id BIGINT UNSIGNED NOT NULL,
    supplier_id BIGINT UNSIGNED NOT NULL,
    unit ENUM('pcs', 'box', 'set', 'kg', 'meter') NOT NULL DEFAULT 'pcs',
    standard_price DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    sales_price DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    sku VARCHAR(64) DEFAULT NULL,
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_products_product_code (product_code),
    UNIQUE KEY uk_products_sku (sku),
    KEY idx_products_category_id (category_id),
    KEY idx_products_supplier_id (supplier_id),
    CONSTRAINT fk_products_category_id FOREIGN KEY (category_id) REFERENCES product_categories (id),
    CONSTRAINT fk_products_supplier_id FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS warehouses (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    warehouse_code VARCHAR(32) NOT NULL,
    warehouse_name VARCHAR(128) NOT NULL,
    location VARCHAR(128) DEFAULT NULL,
    manager_name VARCHAR(64) DEFAULT NULL,
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_warehouses_warehouse_code (warehouse_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS inventory (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    product_id BIGINT UNSIGNED NOT NULL,
    warehouse_id BIGINT UNSIGNED NOT NULL,
    quantity_on_hand INT UNSIGNED NOT NULL DEFAULT 0,
    quantity_reserved INT UNSIGNED NOT NULL DEFAULT 0,
    reorder_level INT UNSIGNED NOT NULL DEFAULT 0,
    last_stocked_at DATETIME DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_inventory_product_warehouse (product_id, warehouse_id),
    KEY idx_inventory_product_id (product_id),
    KEY idx_inventory_warehouse_id (warehouse_id),
    CONSTRAINT fk_inventory_product_id FOREIGN KEY (product_id) REFERENCES products (id),
    CONSTRAINT fk_inventory_warehouse_id FOREIGN KEY (warehouse_id) REFERENCES warehouses (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_opportunities (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    opportunity_code VARCHAR(32) NOT NULL,
    customer_id BIGINT UNSIGNED NOT NULL,
    contact_id BIGINT UNSIGNED DEFAULT NULL,
    title VARCHAR(128) NOT NULL,
    stage ENUM('lead', 'qualified', 'proposal', 'negotiation', 'won', 'lost') NOT NULL DEFAULT 'lead',
    estimated_amount DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    expected_close_date DATE DEFAULT NULL,
    probability TINYINT UNSIGNED NOT NULL DEFAULT 0,
    owner_name VARCHAR(64) DEFAULT NULL,
    notes TEXT DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_sales_opportunities_opportunity_code (opportunity_code),
    KEY idx_sales_opportunities_customer_id (customer_id),
    KEY idx_sales_opportunities_contact_id (contact_id),
    CONSTRAINT fk_sales_opportunities_customer_id FOREIGN KEY (customer_id) REFERENCES customers (id),
    CONSTRAINT fk_sales_opportunities_contact_id FOREIGN KEY (contact_id) REFERENCES contacts (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_orders (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    order_no VARCHAR(32) NOT NULL,
    customer_id BIGINT UNSIGNED NOT NULL,
    contact_id BIGINT UNSIGNED DEFAULT NULL,
    opportunity_id BIGINT UNSIGNED DEFAULT NULL,
    order_status ENUM('draft', 'confirmed', 'fulfilled', 'cancelled') NOT NULL DEFAULT 'draft',
    order_date DATE NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'CNY',
    total_amount DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    payment_status ENUM('unpaid', 'partial', 'paid') NOT NULL DEFAULT 'unpaid',
    shipping_address VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_sales_orders_order_no (order_no),
    KEY idx_sales_orders_customer_id (customer_id),
    KEY idx_sales_orders_contact_id (contact_id),
    KEY idx_sales_orders_opportunity_id (opportunity_id),
    CONSTRAINT fk_sales_orders_customer_id FOREIGN KEY (customer_id) REFERENCES customers (id),
    CONSTRAINT fk_sales_orders_contact_id FOREIGN KEY (contact_id) REFERENCES contacts (id),
    CONSTRAINT fk_sales_orders_opportunity_id FOREIGN KEY (opportunity_id) REFERENCES sales_opportunities (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_order_items (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    sales_order_id BIGINT UNSIGNED NOT NULL,
    product_id BIGINT UNSIGNED NOT NULL,
    quantity INT UNSIGNED NOT NULL,
    unit_price DECIMAL(12, 2) NOT NULL,
    discount_rate DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    line_amount DECIMAL(14, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_sales_order_items_sales_order_id (sales_order_id),
    KEY idx_sales_order_items_product_id (product_id),
    CONSTRAINT fk_sales_order_items_sales_order_id FOREIGN KEY (sales_order_id) REFERENCES sales_orders (id),
    CONSTRAINT fk_sales_order_items_product_id FOREIGN KEY (product_id) REFERENCES products (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS purchase_orders (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    po_no VARCHAR(32) NOT NULL,
    supplier_id BIGINT UNSIGNED NOT NULL,
    warehouse_id BIGINT UNSIGNED NOT NULL,
    po_status ENUM('draft', 'ordered', 'received', 'cancelled') NOT NULL DEFAULT 'draft',
    order_date DATE NOT NULL,
    expected_arrival_date DATE DEFAULT NULL,
    total_amount DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    buyer_name VARCHAR(64) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_purchase_orders_po_no (po_no),
    KEY idx_purchase_orders_supplier_id (supplier_id),
    KEY idx_purchase_orders_warehouse_id (warehouse_id),
    CONSTRAINT fk_purchase_orders_supplier_id FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
    CONSTRAINT fk_purchase_orders_warehouse_id FOREIGN KEY (warehouse_id) REFERENCES warehouses (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS purchase_order_items (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    purchase_order_id BIGINT UNSIGNED NOT NULL,
    product_id BIGINT UNSIGNED NOT NULL,
    quantity INT UNSIGNED NOT NULL,
    unit_cost DECIMAL(12, 2) NOT NULL,
    line_amount DECIMAL(14, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_purchase_order_items_purchase_order_id (purchase_order_id),
    KEY idx_purchase_order_items_product_id (product_id),
    CONSTRAINT fk_purchase_order_items_purchase_order_id FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders (id),
    CONSTRAINT fk_purchase_order_items_product_id FOREIGN KEY (product_id) REFERENCES products (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
