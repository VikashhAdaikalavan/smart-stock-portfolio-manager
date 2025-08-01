package com.example.tradesight;

import javafx.geometry.Insets;
import javafx.geometry.Orientation;
import javafx.geometry.Pos;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.layout.*;
import javafx.scene.web.WebEngine;
import javafx.scene.web.WebView;
import javafx.stage.Stage;

public class analytics_graph {
    public Parent getlayout(String username, Stage window) {

        BorderPane root = new BorderPane();

        VBox sidepane = new VBox(10);
        sidepane.setPadding(new Insets(40, 20, 40, 20));
        sidepane.setPrefWidth(300);
        sidepane.setSpacing(40);
        sidepane.setStyle("-fx-background-color: #2c3e50;");

        Label title = new Label("Portfolio Manager");
        title.setId("sidebar-title");
        title.setAlignment(Pos.TOP_CENTER);

        Button dashboard = new Button("\uD83D\uDCCA Dashboard");
        Button Portfolio = new Button("\uD83D\uDCBC Portfolio");
        Button analysis = new Button("\uD83D\uDCC8 Analysis");
        Button research = new Button("\uD83D\uDD0D Research");

        dashboard.setPrefWidth(180);
        Portfolio.setPrefWidth(180);
        analysis.setPrefWidth(180);
        research.setPrefWidth(180);

        dashboard.getStyleClass().add("sidebar-buttons");
        Portfolio.getStyleClass().add("sidebar-buttons");
        analysis.getStyleClass().add("sidebar-buttons");
        research.getStyleClass().add("sidebar-buttons");

        dashboard.getStyleClass().add("sidebar-item");
        Portfolio.getStyleClass().add("sidebar-item");
        analysis.getStyleClass().add("nav-button-active");
        research.getStyleClass().add("sidebar-item");

        sidepane.getChildren().addAll(title, dashboard, Portfolio, analysis, research);
        sidepane.setAlignment(Pos.TOP_CENTER);
        root.setLeft(sidepane);

        // Search
        Label search = new Label("Search:");
        search.getStyleClass().add("heading");
        TextField stockname = new TextField();
        stockname.setPromptText("\uD83D\uDD0D Enter security name/cc");
        stockname.getStyleClass().add("search-button");
        HBox first = new HBox(10);
        first.setSpacing(50);
        first.getChildren().addAll(search, stockname);

        // Period
        Label period = new Label("Period:");
        period.getStyleClass().add("heading");


        ToggleGroup group = new ToggleGroup();
        RadioButton daily = new RadioButton("Daily");
        RadioButton monthly = new RadioButton("Monthly");
        RadioButton yearly = new RadioButton("Yearly");
        daily.setToggleGroup(group);
        monthly.setToggleGroup(group);
        yearly.setToggleGroup(group);
        daily.getStyleClass().add("buttons");
        monthly.getStyleClass().add("buttons");
        yearly.getStyleClass().add("buttons");

        // Daily Pickers
        DatePicker fromdate = new DatePicker();
        DatePicker todate = new DatePicker();
        fromdate.setPromptText("From");
        todate.setPromptText("To");
        fromdate.getStyleClass().add("search-button");
        todate.getStyleClass().add("search-button");
        HBox date = new HBox(20,daily, fromdate, new Separator(Orientation.VERTICAL), todate);

        // Monthly Pickers
        Label from = new Label("From:");
        from.getStyleClass().add("from");
        ComboBox<String> combobox = new ComboBox<>();
        combobox.getItems().addAll("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec");
        combobox.setPromptText("MMM");
        combobox.getStyleClass().add("combo-box");

        ComboBox<String> combobox1 = new ComboBox<>();
        for (int y = 1991; y <= 2025; y++) combobox1.getItems().add(String.valueOf(y));
        combobox1.setPromptText("YYYY");
        combobox1.getStyleClass().add("combo-box");

        VBox month = new VBox(5, from, combobox, combobox1);
        HBox month1 = new HBox(15,monthly, month);

        // Yearly Picker
        Label from1 = new Label("From:");
        from1.getStyleClass().add("from");
        ComboBox<String> combobox2 = new ComboBox<>();
        combobox2.getItems().addAll(combobox1.getItems());
        combobox2.setPromptText("YYYY");
        combobox2.getStyleClass().add("combo-box");

        VBox year = new VBox(5, from1, combobox2);
        HBox year1 = new HBox(25,yearly ,year);

        // Group date/month/year
        VBox outer = new VBox(15, date, month1, year1);
        outer.setAlignment(Pos.CENTER_LEFT);

        group.selectedToggleProperty().addListener((obs, oldToggle, newToggle) -> {
            if (newToggle != null) {
                String selected = ((RadioButton) newToggle).getText();
                boolean isDaily = selected.equals("Daily");
                boolean isMonthly = selected.equals("Monthly");
                fromdate.setDisable(!isDaily);
                todate.setDisable(!isDaily);
                combobox.setDisable(!isMonthly);
                combobox1.setDisable(!isMonthly);
                combobox2.setDisable(!(selected.equals("Yearly")));
            }
        });

        // Submit Button
        Button submit = new Button("Submit");
        submit.setOnAction(e -> {
            Toggle selectedToggle = group.getSelectedToggle();
            if (selectedToggle == null) return;
            String selectedTimeFrame = ((RadioButton) selectedToggle).getText();
            String stock_name = stockname.getText();

            if (selectedTimeFrame.equals("Daily") && fromdate.getValue() != null && todate.getValue() != null) {
                dashboard_request.stockname_graph(username, stock_name, "daily", fromdate.getValue(), todate.getValue(), null, null);
            } else if (selectedTimeFrame.equals("Monthly") && combobox.getValue() != null && combobox1.getValue() != null) {
                dashboard_request.stockname_graph(username, stock_name, "monthly", null, null, combobox.getValue(), combobox1.getValue());
            } else if (selectedTimeFrame.equals("Yearly") && combobox2.getValue() != null) {
                dashboard_request.stockname_graph(username, stock_name, "yearly", null, null, null, combobox2.getValue());
            }
        });
        submit.getStyleClass().add("submit");

        VBox finalbox = new VBox(20, first, period, outer, submit);
        finalbox.setPadding(new Insets(20));

        WebView top = new WebView();
        top.getEngine().load("file:///C:/Users/varun/OneDrive/Desktop/java_project/candlestick_chart.html");

        WebView bottom_left = new WebView();
        bottom_left.getEngine().load("file:///C:/Users/varun/OneDrive/Desktop/java_project/profit_loss.html");

        WebView bottom_right = new WebView();
        bottom_right.getEngine().load("file:///C:/Users/varun/OneDrive/Desktop/java_project/portfolio_value.html");

        HBox hbox = new HBox(20, bottom_left, bottom_right);

        VBox vbox = new VBox(20, finalbox, top, hbox);
        vbox.getStyleClass().add("root");
        vbox.setPadding(new Insets(20));

        ScrollPane scrollPane = new ScrollPane(vbox);
        scrollPane.setFitToWidth(true);
        scrollPane.setPannable(true);
        root.setCenter(scrollPane);

        Portfolio.setOnAction(event -> {
            portfolio port = new portfolio();
            Scene portscene = new Scene(port.getlayout(username, window),1000,1000);
            portscene.getStylesheets().add(getClass().getResource("/portfolio.css").toExternalForm());
            window.setScene(portscene);
        });

        research.setOnAction(event -> {
            research res = new research();
            Scene resscene = new Scene(res.getlayout(username, window), 1000, 1000);
            resscene.getStylesheets().add(getClass().getResource("/research.css").toExternalForm());
            window.setScene(resscene);
        });

        dashboard.setOnAction(event -> {
            com.example.tradesight.dashboard dash = new  com.example.tradesight.dashboard();
            Scene dashcene = new Scene(dash.getlayout(username,window),1000,1000);
            dashcene.getStylesheets().add(getClass().getResource("/styles.css").toExternalForm());
            window.setScene(dashcene);
        });

        return root;
    }
}
