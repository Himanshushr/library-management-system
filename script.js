// script.js (Full Content)

document.addEventListener('DOMContentLoaded', () => {

    // --- Utility Functions ---
    const getReturnDate = () => {
        const today = new Date();
        const futureDate = new Date();
        // Set return date 15 days in the future (Mock 15-day loan period)
        futureDate.setDate(today.getDate() + 15);
        
        const yyyy = futureDate.getFullYear();
        const mm = String(futureDate.getMonth() + 1).padStart(2, '0');
        const dd = String(futureDate.getDate()).padStart(2, '0');
        return `${yyyy}-${mm}-${dd}`;
    };
    
    const getTodayDate = () => {
        return new Date().toISOString().split('T')[0];
    };

    // --- 1. Login and Password Toggle ---
    const loginForm = document.getElementById('login_form');
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');
    const loginMessage = document.getElementById('login_message');

    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            this.textContent = (type === 'password' ? 'Show' : 'Hide');
        });
    }

    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();

            const username = document.getElementById('username').value;
            const password = passwordInput.value;

            // Mock Authentication for demonstration:
            if (username === 'admin' && password === '1234') {
                loginMessage.textContent = 'Login successful! Redirecting to Admin Dashboard...';
                loginMessage.className = 'success-message';
                setTimeout(() => {
                    window.location.href = '/admin.html';
                }, 500);
            } else if (username === 'user' && password === 'guest') {
                loginMessage.textContent = 'Login successful! Redirecting to Home Page...';
                loginMessage.className = 'success-message';
                setTimeout(() => {
                    window.location.href = '/index.html';
                }, 500);
            } else {
                loginMessage.textContent = 'Invalid username or password.';
                loginMessage.className = 'error-message';
            }
        });
    }

    // --- 2. Handle Book Search ---
    const searchForm = document.getElementById('book_search_form');
    const searchResultsBody = document.getElementById('search_results_body');
    const issueDateInput = document.getElementById('issue_date');
    const returnDateInput = document.getElementById('return_date');

    if (issueDateInput && returnDateInput) {
        // Set dates on the Issue form
        const today = getTodayDate();
        issueDateInput.value = today;
        issueDateInput.min = today; 
        
        returnDateInput.value = getReturnDate();
        returnDateInput.min = today; 
    }

    if (searchForm) {
        searchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = document.getElementById('search_query').value;
            
            const response = await fetch('/api/search_book', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });
            const result = await response.json();
            
            searchResultsBody.innerHTML = '';
            
            if (result.success && result.results.length > 0) {
                result.results.forEach(book => {
                    // Uses 'available_copies' from the DB response
                    const availableCount = book.available_copies || 0; 
                    const availableText = availableCount > 0 ? `Yes (${availableCount} copies)` : 'No';
                    const isDisabled = availableCount <= 0 ? 'disabled' : '';
                    
                    const row = `
                        <tr>
                            <td>${book.title}</td>
                            <td>${book.author}</td>
                            <td>${book.serial_no}</td>
                            <td>${availableText}</td>
                            <td><input type="radio" name="selected_book_id" value="${book.serial_no}" ${isDisabled} required></td>
                        </tr>
                    `;
                    searchResultsBody.innerHTML += row;
                });
            } else {
                searchResultsBody.innerHTML = '<tr><td colspan="5">No books found or search field empty.</td></tr>';
            }
        });
    }

    // --- 3. Handle Book Issue ---
    const issueForm = document.getElementById('book_issue_form');
    const issueMessage = document.getElementById('issue_message');

    if (issueForm) {
        issueForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const selectedRadio = document.querySelector('input[name="selected_book_id"]:checked');
            if (!selectedRadio) {
                issueMessage.textContent = "Error: Please select a book from the search results first.";
                issueMessage.className = 'error-message';
                return;
            }
            
            const user_id = document.getElementById('user_id_i').value;
            if (!user_id) {
                issueMessage.textContent = "Error: User ID is required.";
                issueMessage.className = 'error-message';
                return;
            }

            const loanData = {
                book_id: selectedRadio.value,
                user_id: user_id, 
                issue_date: issueDateInput.value,
                return_date: returnDateInput.value
            };

            const response = await fetch('/api/issue_book', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(loanData)
            });
            const result = await response.json();
            
            issueMessage.textContent = result.message;
            issueMessage.className = result.success ? 'success-message' : 'error-message';
        });
    }

    // --- 4. Handle Return Book ---
    const returnForm = document.getElementById('return_book_form');
    const returnMessage = document.getElementById('return_message');

    if (returnForm) {
        const returnDateR = document.getElementById('return_date_r');
        if (returnDateR) {
            returnDateR.value = getTodayDate();
            returnDateR.min = getTodayDate(); 
        }

        returnForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const serial_no = document.getElementById('serial_no_r').value;
            const return_date = document.getElementById('return_date_r').value;

            const returnData = {
                serial_no: serial_no,
                return_date: return_date
            };

            const response = await fetch('/api/return_book', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(returnData)
            });
            const result = await response.json();

            if (result.success) {
                if (result.fine_amount > 0) {
                    // Redirect using transaction_id for DB lookup
                    alert(`Return successful, but a fine of $${result.fine_amount.toFixed(2)} is due. Redirecting to payment.`);
                    window.location.href = `/fine_payment.html?fine=${result.fine_amount.toFixed(2)}&transaction_id=${result.transaction_id}`; 
                } else {
                    // Final confirmation handled by DB update in app.py logic
                    returnMessage.textContent = `Success: ${result.book_title} returned successfully. No fine applied.`;
                    returnMessage.className = 'success-message';
                }
            } else {
                returnMessage.textContent = `Error: ${result.message}`;
                returnMessage.className = 'error-message';
            }
        });
    }


    // --- 5. Handle Fine Payment ---
    const finePaymentForm = document.getElementById('fine_payment_form');
    const fineMessage = document.getElementById('fine_message');
    const transactionIdInput = document.getElementById('loan_index_h'); // Renamed ID, but HTML may still use loan_index_h
    const calculatedFineInput = document.getElementById('calculated_fine');

    if (finePaymentForm) {
        const urlParams = new URLSearchParams(window.location.search);
        const fineAmount = urlParams.get('fine');
        const transactionId = urlParams.get('transaction_id'); 

        if (transactionId && fineAmount) {
            transactionIdInput.value = transactionId;
            calculatedFineInput.value = `${fineAmount} INR`;
            document.getElementById('fine_paid').value = fineAmount; 
        } else {
            // Handle scenario if user navigated directly without fine
            transactionIdInput.value = '-1';
        }

        finePaymentForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const paymentData = {
                // Pass transaction_id to the API
                transaction_id: transactionIdInput.value, 
                fine_paid: parseFloat(document.getElementById('fine_paid').value),
                remarks: document.getElementById('remarks_fine').value,
                pending_fine: document.getElementById('pending_fine').checked
            };

            const response = await fetch('/api/confirm_fine', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(paymentData)
            });
            const result = await response.json();

            fineMessage.textContent = result.message;
            fineMessage.className = result.success ? 'success-message' : 'error-message';
            
            if (result.success) {
                finePaymentForm.querySelector('button[type="submit"]').disabled = true;
            }
        });
    }

    // --- 6. Handle Membership Forms ---

    // 6.1 Add Membership
    const addMembershipForm = document.getElementById('add_membership_form');
    const addMemberMessage = document.getElementById('add_member_message');

    if (addMembershipForm) {
        addMembershipForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const selectedDuration = document.querySelector('input[name="duration"]:checked');
            if (!selectedDuration) return;

            const data = {
                name: document.getElementById('member_name').value,
                membership_type: selectedDuration.value
            };

            const response = await fetch('/api/add_membership', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();

            addMemberMessage.textContent = result.message;
            addMemberMessage.className = result.success ? 'success-message' : 'error-message';
            if (result.success) addMembershipForm.reset();
        });
    }

    // 6.2 Update/Extend Membership
    const updateMembershipForm = document.getElementById('update_membership_form');
    const updateMemberMessage = document.getElementById('update_member_message');

    if (updateMembershipForm) {
        updateMembershipForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const data = {
                user_id: document.getElementById('update_user_id').value,
                extension: '6 months' 
            };

            const response = await fetch('/api/update_membership', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();

            updateMemberMessage.textContent = result.message;
            updateMemberMessage.className = result.success ? 'success-message' : 'error-message';
        });
    }

    // 6.3 User Management (View/Fetch)
    const userManagementForm = document.getElementById('user_management_form');
    const userManageMessage = document.getElementById('user_manage_message');
    const userDetailsDisplay = document.getElementById('user_details_display');
    const userDetailsPre = document.getElementById('user_details_pre');

    if (userManagementForm) {
        userManagementForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const selectedOption = document.querySelector('input[name="user_option"]:checked').value;
            const userId = document.getElementById('manage_user_id').value;

            const data = {
                user_id: userId,
                action: selectedOption
            };

            const response = await fetch('/api/manage_user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();

            userManageMessage.textContent = result.message;
            userManageMessage.className = result.success ? 'success-message' : 'error-message';
            userDetailsDisplay.style.display = 'none';

            if (result.success && result.user_details) {
                userDetailsPre.textContent = JSON.stringify(result.user_details, null, 2);
                userDetailsDisplay.style.display = 'block';
            }
        });
    }

    // --- 7. Handle Admin Maintenance ---
    const addBookForm = document.getElementById('add_book_form');
    const addBookMessage = document.getElementById('add_book_message');

    if (addBookForm) {
        addBookForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const bookData = {
                title: document.getElementById('book_title').value,
                author: document.getElementById('book_author').value,
                serial_no: document.getElementById('book_serial_no').value,
                available: document.getElementById('book_available').value 
            };

            const response = await fetch('/api/add_book', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(bookData)
            });
            const result = await response.json();

            addBookMessage.textContent = result.message;
            addBookMessage.className = result.success ? 'success-message' : 'error-message';

            if (result.success) {
                addBookForm.reset();
            }
        });
    }
});