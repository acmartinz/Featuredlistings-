import java.util.Scanner;
import java.time.Year;

public class AgeCalculator {
    public static void main(String[] args) {
        // Create Scanner object
        Scanner scanner = new Scanner(System.in);

        // Get the current year
        int currentYear = Year.now().getValue();

        // Ask the user for their birth year
        System.out.print("Enter your birth year: ");
        int birthYear = scanner.nextInt();

        // Calculate age
        int age = currentYear - birthYear;

        // Display the result
        System.out.println("Your current age is: " + age);

        // Close the scanner
        scanner.close();
    }
}