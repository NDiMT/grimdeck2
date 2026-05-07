extends Control

const CARD_SCENE := preload("res://scenes/card.tscn")
const HAND_LIMIT := 7

@onready var hand: HBoxContainer = $UI/Hand
@onready var draw_button: Button = $UI/Bar/DrawButton
@onready var end_turn_button: Button = $UI/Bar/EndTurnButton
@onready var status_label: Label = $UI/Bar/StatusLabel
@onready var log_label: Label = $UI/LogLabel

var deck: Array[CardData] = []
var discard_pile: Array[CardData] = []


func _ready() -> void:
	deck = _starter_deck()
	deck.shuffle()
	draw_button.pressed.connect(_on_draw_pressed)
	end_turn_button.pressed.connect(_on_end_turn_pressed)
	_log("A hush falls over the table. Draw your hand.")
	_refresh_status()


func _on_draw_pressed() -> void:
	if hand.get_child_count() >= HAND_LIMIT:
		_log("Hand is full.")
		return
	if deck.is_empty():
		if discard_pile.is_empty():
			_log("No cards left to draw.")
			return
		deck = discard_pile
		discard_pile = []
		deck.shuffle()
		_log("Discard pile reshuffled into the deck.")
	var card_data: CardData = deck.pop_back()
	var card := CARD_SCENE.instantiate() as Card
	card.set_data(card_data)
	card.played.connect(_on_card_played)
	hand.add_child(card)
	_refresh_status()


func _on_card_played(card: Card) -> void:
	var data := card.data
	var line := "Played %s" % data.card_name
	if data.damage > 0:
		line += " — %d damage" % data.damage
	if data.block > 0:
		line += " — %d block" % data.block
	_log(line + ".")
	discard_pile.append(data)
	card.queue_free()
	_refresh_status.call_deferred()


func _on_end_turn_pressed() -> void:
	var discarded := 0
	for c in hand.get_children():
		var card := c as Card
		discard_pile.append(card.data)
		card.queue_free()
		discarded += 1
	if discarded > 0:
		_log("Turn ended. %d card(s) discarded." % discarded)
	else:
		_log("Turn ended.")
	_refresh_status.call_deferred()


func _refresh_status() -> void:
	status_label.text = "Deck %d  •  Discard %d  •  Hand %d/%d" % [
		deck.size(), discard_pile.size(), hand.get_child_count(), HAND_LIMIT
	]


func _log(line: String) -> void:
	log_label.text = line


func _starter_deck() -> Array[CardData]:
	var cards: Array[CardData] = []
	for i in 4:
		cards.append(_make_card("Strike", "Deal 6 damage.", 1, 6, 0))
	for i in 4:
		cards.append(_make_card("Defend", "Gain 5 block.", 1, 0, 5))
	cards.append(_make_card("Dread", "Deal 12 damage.", 2, 12, 0))
	cards.append(_make_card("Bulwark", "Gain 10 block.", 2, 0, 10))
	return cards


func _make_card(card_name: String, desc: String, cost: int, damage: int, block: int) -> CardData:
	var c := CardData.new()
	c.card_name = card_name
	c.description = desc
	c.cost = cost
	c.damage = damage
	c.block = block
	return c
