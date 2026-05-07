class_name Card
extends PanelContainer

signal played(card: Card)

var data: CardData

@onready var name_label: Label = $Margin/VBox/NameLabel
@onready var cost_label: Label = $Margin/VBox/CostLabel
@onready var desc_label: Label = $Margin/VBox/DescLabel


func _ready() -> void:
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	if data:
		_refresh()


func set_data(new_data: CardData) -> void:
	data = new_data
	if is_node_ready():
		_refresh()


func _refresh() -> void:
	name_label.text = data.card_name
	cost_label.text = "Cost %d" % data.cost
	desc_label.text = data.description


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		played.emit(self)
