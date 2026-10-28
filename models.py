from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    quotation_no = Column(String(100), unique=True, index=True, nullable=False)
    company_name = Column(String(255), default="WARDHAN TRADING EST.")
    date = Column(String(100), default="24/9/2020")
    customer_name = Column(String(255), nullable=False, default="Radisson Blue Hotel, Kuwait")
    total_amount = Column(Float, default=0.0)
    total_kd = Column(Integer, default=0)
    total_fills = Column(Integer, default=0)
    amount_in_words = Column(String(255), default="KD Twenty Five")
    incharge = Column(String(255), default="")
    email = Column(String(255), default="thilakantmt@gmail.com")
    phone = Column(String(255), default="+965 99983543")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan", order_by="QuotationItem.item_order")

    def to_dict(self):
        return {
            "id": self.id,
            "quotation_no": self.quotation_no,
            "company_name": self.company_name,
            "date": self.date,
            "customer_name": self.customer_name,
            "total_amount": self.total_amount,
            "total_kd": self.total_kd,
            "total_fills": self.total_fills,
            "amount_in_words": self.amount_in_words,
            "incharge": self.incharge,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else "",
            "items": [item.to_dict() for item in self.items]
        }

class QuotationItem(Base):
    __tablename__ = "quotation_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False)
    item_order = Column(Integer, default=1)
    description = Column(Text, nullable=False, default="")
    quantity = Column(Float, default=1.0)
    unit_price_kd = Column(Integer, default=0)
    unit_price_fills = Column(Integer, default=0)
    total_kd = Column(Integer, default=0)
    total_fills = Column(Integer, default=0)
    total_price = Column(Float, default=0.0)

    quotation = relationship("Quotation", back_populates="items")

    def to_dict(self):
        return {
            "id": self.id,
            "item_order": self.item_order,
            "description": self.description,
            "quantity": self.quantity,
            "unit_price_kd": self.unit_price_kd,
            "unit_price_fills": self.unit_price_fills,
            "total_kd": self.total_kd,
            "total_fills": self.total_fills,
            "total_price": self.total_price
        }
