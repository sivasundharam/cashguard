from fastapi import APIRouter, HTTPException

from app.services.mongodb import invoices_col

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


@router.get("")
async def list_invoices():
    return await invoices_col().find({}, {"_id": 0}).to_list(None)


@router.get("/overdue")
async def list_overdue():
    return (
        await invoices_col()
        .find({"status": "overdue"}, {"_id": 0})
        .sort("days_overdue", -1)
        .to_list(None)
    )


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str):
    inv = await invoices_col().find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return inv
