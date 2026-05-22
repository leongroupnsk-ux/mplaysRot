"""
/v1/canvas — Attribly Canvas: boards, widgets, connections, templates, widget data, AI.
"""
import secrets
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.canvas import BoardConnection, BoardTemplate, BoardWidget, CanvasBoard
from app.models.campaign import Campaign
from app.models.catalog import Product, Store
from app.models.user import User
from app.schemas.canvas import (
    AICommandRequest, AICommandResponse,
    BoardCreate, BoardDetailOut, BoardOut, BoardUpdate,
    CampaignWidgetData, ConnectionCreate, ConnectionOut,
    LogisticsWidgetData, ProductWidgetData,
    TemplateOut, WidgetBulkUpdate, WidgetCreate, WidgetOut, WidgetUpdate,
)
from app.utils.deps import get_current_user

router = APIRouter()


# ── Boards ────────────────────────────────────────────────────────────────────

@router.get("/boards", response_model=list[BoardOut])
async def list_boards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = await db.execute(
        select(CanvasBoard)
        .where(CanvasBoard.user_id == current_user.id)
        .order_by(CanvasBoard.updated_at.desc())
    )
    return r.scalars().all()


@router.post("/boards", response_model=BoardDetailOut, status_code=201)
async def create_board(
    payload: BoardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template_data: dict = {"widgets": [], "connections": []}

    # If creating from a template, clone its widgets
    if payload.template_id:
        try:
            tid = uuid.UUID(payload.template_id)
        except ValueError:
            raise HTTPException(400, detail="Invalid template_id")
        tpl_r = await db.execute(select(BoardTemplate).where(BoardTemplate.id == tid))
        tpl = tpl_r.scalar_one_or_none()
        if tpl:
            template_data = tpl.template_data or {"widgets": [], "connections": []}

    board = CanvasBoard(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        template_id=uuid.UUID(payload.template_id) if payload.template_id else None,
    )
    db.add(board)
    await db.flush()  # get board.id

    created_widgets: dict[str, BoardWidget] = {}
    old_to_new: dict[str, str] = {}  # template widget id → new widget id

    for w_data in template_data.get("widgets", []):
        w = BoardWidget(
            board_id=board.id,
            widget_type=w_data.get("type", "sticker"),
            x=w_data.get("x", 100),
            y=w_data.get("y", 100),
            width=w_data.get("width", 300),
            height=w_data.get("height", 200),
            z_index=w_data.get("z_index", 0),
            data=w_data.get("data", {}),
            style=w_data.get("style", {}),
        )
        db.add(w)
        await db.flush()
        old_id = w_data.get("id", "")
        old_to_new[old_id] = str(w.id)
        created_widgets[str(w.id)] = w

    connections_out: list[BoardConnection] = []
    for c_data in template_data.get("connections", []):
        from_id = old_to_new.get(c_data.get("from_widget_id", ""))
        to_id = old_to_new.get(c_data.get("to_widget_id", ""))
        if from_id and to_id:
            conn = BoardConnection(
                board_id=board.id,
                from_widget_id=uuid.UUID(from_id),
                to_widget_id=uuid.UUID(to_id),
                style=c_data.get("style", {}),
                label=c_data.get("label"),
            )
            db.add(conn)
            connections_out.append(conn)

    await db.commit()
    await db.refresh(board)

    return BoardDetailOut(
        **BoardOut.model_validate(board).model_dump(),
        widgets=[WidgetOut.model_validate(w) for w in created_widgets.values()],
        connections=[ConnectionOut.model_validate(c) for c in connections_out],
    )


@router.get("/boards/{board_id}", response_model=BoardDetailOut)
async def get_board(
    board_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        bid = uuid.UUID(board_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid board_id")

    board_r = await db.execute(
        select(CanvasBoard).where(CanvasBoard.id == bid, CanvasBoard.user_id == current_user.id)
    )
    board = board_r.scalar_one_or_none()
    if not board:
        raise HTTPException(404, detail="Board not found")

    widgets_r = await db.execute(
        select(BoardWidget).where(BoardWidget.board_id == bid).order_by(BoardWidget.z_index, BoardWidget.created_at)
    )
    widgets = widgets_r.scalars().all()

    conns_r = await db.execute(
        select(BoardConnection).where(BoardConnection.board_id == bid)
    )
    connections = conns_r.scalars().all()

    return BoardDetailOut(
        **BoardOut.model_validate(board).model_dump(),
        widgets=[WidgetOut.model_validate(w) for w in widgets],
        connections=[ConnectionOut.model_validate(c) for c in connections],
    )


@router.patch("/boards/{board_id}", response_model=BoardOut)
async def update_board(
    board_id: str,
    payload: BoardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        bid = uuid.UUID(board_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid board_id")

    r = await db.execute(
        select(CanvasBoard).where(CanvasBoard.id == bid, CanvasBoard.user_id == current_user.id)
    )
    board = r.scalar_one_or_none()
    if not board:
        raise HTTPException(404, detail="Board not found")

    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(board, k, v)

    from datetime import datetime, timezone
    board.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(board)
    return board


@router.delete("/boards/{board_id}", status_code=204)
async def delete_board(
    board_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        bid = uuid.UUID(board_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid board_id")

    r = await db.execute(
        select(CanvasBoard).where(CanvasBoard.id == bid, CanvasBoard.user_id == current_user.id)
    )
    board = r.scalar_one_or_none()
    if not board:
        raise HTTPException(404, detail="Board not found")
    await db.delete(board)
    await db.commit()


@router.post("/boards/{board_id}/share", response_model=BoardOut)
async def toggle_share(
    board_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle public share link. Returns board with share_token."""
    try:
        bid = uuid.UUID(board_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid board_id")

    r = await db.execute(
        select(CanvasBoard).where(CanvasBoard.id == bid, CanvasBoard.user_id == current_user.id)
    )
    board = r.scalar_one_or_none()
    if not board:
        raise HTTPException(404, detail="Board not found")

    if board.is_public:
        board.is_public = False
        board.share_token = None
    else:
        board.is_public = True
        board.share_token = secrets.token_urlsafe(32)

    await db.commit()
    await db.refresh(board)
    return board


# ── Widgets ───────────────────────────────────────────────────────────────────

@router.post("/boards/{board_id}/widgets", response_model=WidgetOut, status_code=201)
async def add_widget(
    board_id: str,
    payload: WidgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        bid = uuid.UUID(board_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid board_id")

    board_r = await db.execute(
        select(CanvasBoard).where(CanvasBoard.id == bid, CanvasBoard.user_id == current_user.id)
    )
    if not board_r.scalar_one_or_none():
        raise HTTPException(404, detail="Board not found")

    widget = BoardWidget(
        board_id=bid,
        widget_type=payload.widget_type,
        x=payload.x,
        y=payload.y,
        width=payload.width,
        height=payload.height,
        z_index=payload.z_index,
        data=payload.data,
        style=payload.style,
    )
    db.add(widget)
    await db.commit()
    await db.refresh(widget)
    return widget


@router.patch("/boards/{board_id}/widgets/{widget_id}", response_model=WidgetOut)
async def update_widget(
    board_id: str,
    widget_id: str,
    payload: WidgetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        bid = uuid.UUID(board_id)
        wid = uuid.UUID(widget_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid ID")

    # Verify board ownership
    board_r = await db.execute(
        select(CanvasBoard).where(CanvasBoard.id == bid, CanvasBoard.user_id == current_user.id)
    )
    if not board_r.scalar_one_or_none():
        raise HTTPException(404, detail="Board not found")

    r = await db.execute(select(BoardWidget).where(BoardWidget.id == wid, BoardWidget.board_id == bid))
    widget = r.scalar_one_or_none()
    if not widget:
        raise HTTPException(404, detail="Widget not found")

    updates = payload.model_dump(exclude_none=True)
    for k, v in updates.items():
        setattr(widget, k, v)

    from datetime import datetime, timezone
    widget.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(widget)
    return widget


@router.post("/boards/{board_id}/widgets/bulk", status_code=204)
async def bulk_update_widgets(
    board_id: str,
    payload: WidgetBulkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Batch update widget positions after drag operations."""
    try:
        bid = uuid.UUID(board_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid board_id")

    board_r = await db.execute(
        select(CanvasBoard).where(CanvasBoard.id == bid, CanvasBoard.user_id == current_user.id)
    )
    if not board_r.scalar_one_or_none():
        raise HTTPException(404, detail="Board not found")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    for upd in payload.updates:
        try:
            wid = uuid.UUID(str(upd["id"]))
        except (KeyError, ValueError):
            continue
        r = await db.execute(select(BoardWidget).where(BoardWidget.id == wid, BoardWidget.board_id == bid))
        widget = r.scalar_one_or_none()
        if not widget:
            continue
        for k in ("x", "y", "z_index", "width", "height"):
            if k in upd:
                setattr(widget, k, upd[k])
        widget.updated_at = now

    await db.commit()


@router.delete("/boards/{board_id}/widgets/{widget_id}", status_code=204)
async def delete_widget(
    board_id: str,
    widget_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        bid = uuid.UUID(board_id)
        wid = uuid.UUID(widget_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid ID")

    board_r = await db.execute(
        select(CanvasBoard).where(CanvasBoard.id == bid, CanvasBoard.user_id == current_user.id)
    )
    if not board_r.scalar_one_or_none():
        raise HTTPException(404, detail="Board not found")

    r = await db.execute(select(BoardWidget).where(BoardWidget.id == wid, BoardWidget.board_id == bid))
    widget = r.scalar_one_or_none()
    if not widget:
        raise HTTPException(404, detail="Widget not found")
    await db.delete(widget)
    await db.commit()


# ── Connections ───────────────────────────────────────────────────────────────

@router.post("/boards/{board_id}/connections", response_model=ConnectionOut, status_code=201)
async def add_connection(
    board_id: str,
    payload: ConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        bid = uuid.UUID(board_id)
        from_id = uuid.UUID(payload.from_widget_id)
        to_id = uuid.UUID(payload.to_widget_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid ID")

    board_r = await db.execute(
        select(CanvasBoard).where(CanvasBoard.id == bid, CanvasBoard.user_id == current_user.id)
    )
    if not board_r.scalar_one_or_none():
        raise HTTPException(404, detail="Board not found")

    conn = BoardConnection(
        board_id=bid,
        from_widget_id=from_id,
        to_widget_id=to_id,
        style=payload.style,
        label=payload.label,
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)
    return conn


@router.delete("/boards/{board_id}/connections/{conn_id}", status_code=204)
async def delete_connection(
    board_id: str,
    conn_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        bid = uuid.UUID(board_id)
        cid = uuid.UUID(conn_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid ID")

    board_r = await db.execute(
        select(CanvasBoard).where(CanvasBoard.id == bid, CanvasBoard.user_id == current_user.id)
    )
    if not board_r.scalar_one_or_none():
        raise HTTPException(404, detail="Board not found")

    r = await db.execute(
        select(BoardConnection).where(BoardConnection.id == cid, BoardConnection.board_id == bid)
    )
    conn = r.scalar_one_or_none()
    if not conn:
        raise HTTPException(404, detail="Connection not found")
    await db.delete(conn)
    await db.commit()


# ── Templates ─────────────────────────────────────────────────────────────────

@router.get("/templates", response_model=list[TemplateOut])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    r = await db.execute(select(BoardTemplate).order_by(BoardTemplate.created_at))
    return r.scalars().all()


# ── Live widget data ──────────────────────────────────────────────────────────

@router.get("/widget-data/product", response_model=ProductWidgetData)
async def product_widget_data(
    store_id: str,
    external_product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        sid = uuid.UUID(store_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid store_id")

    store_r = await db.execute(
        select(Store).where(Store.id == sid, Store.user_id == current_user.id)
    )
    store = store_r.scalar_one_or_none()
    if not store:
        raise HTTPException(404, detail="Store not found")

    prod_r = await db.execute(
        select(Product).where(
            Product.store_id == sid,
            Product.external_product_id == external_product_id,
        )
    )
    product = prod_r.scalar_one_or_none()
    if not product:
        raise HTTPException(404, detail="Product not found")

    return ProductWidgetData(
        external_product_id=product.external_product_id,
        title=product.title,
        image_url=product.image_url,
        price=str(product.price) if product.price else None,
        stock=product.stock or 0,
        store_name=store.name,
        marketplace=store.provider,
    )


@router.get("/widget-data/logistics", response_model=LogisticsWidgetData)
async def logistics_widget_data(
    store_id: str,
    external_product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        sid = uuid.UUID(store_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid store_id")

    store_r = await db.execute(
        select(Store).where(Store.id == sid, Store.user_id == current_user.id)
    )
    if not store_r.scalar_one_or_none():
        raise HTTPException(404, detail="Store not found")

    prod_r = await db.execute(
        select(Product).where(
            Product.store_id == sid,
            Product.external_product_id == external_product_id,
        )
    )
    product = prod_r.scalar_one_or_none()
    if not product:
        raise HTTPException(404, detail="Product not found")

    stock = product.stock or 0
    # Rough heuristic: <7 days critical, 7–14 warn, >14 ok
    # (In real implementation, use sales velocity from analytics)
    days_supply = None
    status = "ok" if stock > 30 else ("warn" if stock > 10 else "critical")

    return LogisticsWidgetData(
        external_product_id=product.external_product_id,
        title=product.title,
        image_url=product.image_url,
        stock=stock,
        days_supply=days_supply,
        status=status,
    )


@router.get("/widget-data/campaign", response_model=CampaignWidgetData)
async def campaign_widget_data(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        cid = uuid.UUID(campaign_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid campaign_id")

    r = await db.execute(
        select(Campaign).where(Campaign.id == cid, Campaign.user_id == current_user.id)
    )
    campaign = r.scalar_one_or_none()
    if not campaign:
        raise HTTPException(404, detail="Campaign not found")

    return CampaignWidgetData(
        campaign_id=str(campaign.id),
        name=campaign.name,
        marketplace=campaign.marketplace,
        ad_platform=campaign.ad_platform,
        is_active=campaign.is_active,
        budget=str(campaign.budget) if campaign.budget else None,
        utm_source=campaign.utm_source,
    )


# ── AI assistant ──────────────────────────────────────────────────────────────

@router.post("/boards/{board_id}/ai-command", response_model=AICommandResponse)
async def ai_command(
    board_id: str,
    payload: AICommandRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Parse a natural-language canvas command and return structured actions.
    MVP: keyword-based pattern matching. Production: OpenAI function calling.
    """
    try:
        bid = uuid.UUID(board_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid board_id")

    board_r = await db.execute(
        select(CanvasBoard).where(CanvasBoard.id == bid, CanvasBoard.user_id == current_user.id)
    )
    if not board_r.scalar_one_or_none():
        raise HTTPException(404, detail="Board not found")

    cmd = payload.command.lower()
    actions: list[dict] = []
    message = ""

    # Pattern: add sticker / заметку
    if any(k in cmd for k in ("стикер", "заметк", "note", "sticker")):
        actions.append({
            "type": "add_widget",
            "widget_type": "sticker",
            "x": 200, "y": 200, "width": 200, "height": 150,
            "data": {"content": "📝 Новая заметка", "color": "#FFF3D6"},
            "style": {},
        })
        message = "Добавил стикер на холст."

    # Pattern: add product / товар
    elif any(k in cmd for k in ("товар", "product", "карточк")):
        actions.append({
            "type": "add_widget",
            "widget_type": "product_card",
            "x": 300, "y": 200, "width": 280, "height": 360,
            "data": {},
            "style": {},
        })
        message = "Добавил карточку товара. Настройте SKU в виджете."

    # Pattern: logistics / склад / остатки
    elif any(k in cmd for k in ("склад", "остатк", "logistics", "запас")):
        actions.append({
            "type": "add_widget",
            "widget_type": "logistics",
            "x": 400, "y": 200, "width": 260, "height": 220,
            "data": {},
            "style": {},
        })
        message = "Добавил логистический виджет. Выберите товар для отображения остатков."

    # Pattern: campaign / реклама / кампания
    elif any(k in cmd for k in ("реклам", "кампани", "campaign", "romi")):
        actions.append({
            "type": "add_widget",
            "widget_type": "ad_connector",
            "x": 500, "y": 200, "width": 260, "height": 200,
            "data": {},
            "style": {},
        })
        message = "Добавил рекламный коннектор. Привяжите кампанию для отображения метрик."

    # Pattern: chart / график
    elif any(k in cmd for k in ("график", "chart", "продаж")):
        actions.append({
            "type": "add_widget",
            "widget_type": "mini_chart",
            "x": 300, "y": 300, "width": 340, "height": 200,
            "data": {"metric": "sales", "period": "7d"},
            "style": {},
        })
        message = "Добавил мини-график продаж."

    # Pattern: connect / соедини
    elif any(k in cmd for k in ("соедин", "connect", "связ")):
        message = (
            "Для соединения виджетов: удерживайте Shift и кликните на первый виджет, "
            "затем кликните на второй. Линия будет создана автоматически."
        )

    # Pattern: clean / очист
    elif any(k in cmd for k in ("очист", "clear", "удал всё")):
        message = "Для очистки холста используйте кнопку «•••» в тулбаре → «Очистить холст»."

    else:
        message = (
            f"Понял: «{payload.command}». "
            "Попробуйте команды: «добавь стикер», «добавь карточку товара», "
            "«покажи логистику», «добавь график продаж», «добавь рекламу»."
        )

    return AICommandResponse(message=message, actions=actions)
