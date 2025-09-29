# app/callbacks/callback_sat_applications.py
import sys
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import callback_context, html, dcc

## Internal Scripts
sys.path.append("../../")

# Get styles
from app.styles.styles_sat_explained import (_fact_button_collapsed__style, _fact_button_expanded__style,
                                            _fact_button_expanded_text__style, _fact_button_title__style,
                                             _fact_button_launch_detail__style)
# Get button details
from app.content.content_buttons import (fact_data)

def get_callbacks(app):

    def create_button_callbacks(section):
        """
        Factory function to create callback for a specific section's buttons
        """

        @app.callback(
            [Output(f'sat-{section}-btn-1', 'children'),
             Output(f'sat-{section}-btn-2', 'children'),
             Output(f'sat-{section}-btn-3', 'children'),
             Output(f'sat-{section}-btn-4', 'children'),
             Output(f'sat-{section}-btn-1', 'style'),
             Output(f'sat-{section}-btn-2', 'style'),
             Output(f'sat-{section}-btn-3', 'style'),
             Output(f'sat-{section}-btn-4', 'style')],
            [Input(f'sat-{section}-btn-1', 'n_clicks'),
             Input(f'sat-{section}-btn-2', 'n_clicks'),
             Input(f'sat-{section}-btn-3', 'n_clicks'),
             Input(f'sat-{section}-btn-4', 'n_clicks')],
            [State(f'sat-{section}-btn-1', 'children'),
             State(f'sat-{section}-btn-2', 'children'),
             State(f'sat-{section}-btn-3', 'children'),
             State(f'sat-{section}-btn-4', 'children'),
             State(f'sat-{section}-btn-1', 'style'),
             State(f'sat-{section}-btn-2', 'style'),
             State(f'sat-{section}-btn-3', 'style'),
             State(f'sat-{section}-btn-4', 'style')]
        )
        def update_button_content(click_btn_1, click_btn_2, click_btn_3, click_btn_4,
                                  content_btn_1, content_btn_2, content_btn_3, content_btn_4,
                                  style_btn_1, style_btn_2, style_btn_3, style_btn_4):
            if all(click is None for click in [click_btn_1, click_btn_2, click_btn_3, click_btn_4]):
                raise PreventUpdate

            # Get button number that was clicked
            ctx = callback_context
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
            btn_number = triggered_id.replace(f"sat-{section}-", "")

            # Get current button styles
            button_styles = [style_btn_1, style_btn_2, style_btn_3, style_btn_4]

            # Get the data for this section
            btn_text_dict = fact_data[section]

            # Create button titles (these will be used when buttons are collapsed)
            button_titles = [btn_text_dict[btn_id]["button_title"] for btn_id in ["btn-1", "btn-2", "btn-3", "btn-4"]]

            # Format text for expanded buttons
            def create_text_obj(btn_id):
                text_output = """
                            **[{sat_name}]({nasa_link})**                          
                            **{launch_date_label}**: {launch_date}

                            • {fact_1}\n 
                            • {fact_2}\n 
                            • {fact_3}\n
                            """.format(
                    sat_name=btn_text_dict[btn_id]["sat_name"],
                    nasa_link=btn_text_dict[btn_id]["nasa_link"],
                    launch_date_label="First Launch" if section == "launches" else "Launch Date",
                    launch_date=btn_text_dict[btn_id]["launch_date"],
                    fact_1=btn_text_dict[btn_id]["fact_1"],
                    fact_2=btn_text_dict[btn_id]["fact_2"],
                    fact_3=btn_text_dict[btn_id]["fact_3"]
                )
                return dcc.Markdown(
                    text_output,
                    style={**_fact_button_expanded_text__style}
                )

            # Start with current content/state
            button_contents = [content_btn_1, content_btn_2, content_btn_3, content_btn_4]

            # Update button based on which one was clicked
            btn_index = int(btn_number[-1]) - 1  # Convert btn-1, btn-2, etc. to array index 0, 1, etc.

            # Check if any other buttons are expanded by checking if it's a string (title) or object (markdown)
            is_other_buttons_expanded_list = []
            for i, content in enumerate(button_contents):
                if i != btn_index:
                    is_other_buttons_expanded_list.append(
                        not isinstance(content, str) and not isinstance(content,html.Div)
                    )

            # Check if button is already expanded by checking if it's a string (title) or object (markdown)
            is_expanded = not isinstance(button_contents[btn_index], str) and not isinstance(button_contents[btn_index],
                                                                                             html.Div)

            print("Return button contents: ", button_contents[btn_index])
            if True in is_other_buttons_expanded_list:
                # If any other button is expanded - do nothing
                return button_contents + button_styles
            elif is_expanded:
                # Button is expanded - collapse it
                button_contents[btn_index] = button_titles[btn_index]
                button_styles[btn_index] = {**_fact_button_collapsed__style}
            else:
                # Button is collapsed - expand it
                button_contents[btn_index] = create_text_obj(btn_number)
                button_styles[btn_index] = {**_fact_button_expanded__style}

            # Return updated button content and styles
            return button_contents + button_styles

    # Create callbacks for each section
    create_button_callbacks("history")
    create_button_callbacks("purpose")
    create_button_callbacks("launches")