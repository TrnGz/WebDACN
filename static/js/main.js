// Main Ajax Handler for Flask E-commerce Application
// Handles all forms with smooth user experience

class AjaxHandler {
  constructor() {
    this.init()
    this.setupEventListeners()
  }

  init() {
    // Show loading spinner
    this.createLoadingSpinner()
    // Setup CSRF token if needed
    this.setupCSRF()
  }

  createLoadingSpinner() {
    if (!document.getElementById("loadingSpinner")) {
      const spinner = document.createElement("div")
      spinner.id = "loadingSpinner"
      spinner.innerHTML = `
                <div class="spinner-overlay">
                    <div class="spinner">
                        <div class="bounce1"></div>
                        <div class="bounce2"></div>
                        <div class="bounce3"></div>
                    </div>
                    <p>Đang xử lý...</p>
                </div>
            `
      document.body.appendChild(spinner)
    }
  }

  setupCSRF() {
    // Get CSRF token from meta tag if exists
    const csrfToken = document.querySelector('meta[name="csrf-token"]')
    if (csrfToken) {
      this.csrfToken = csrfToken.getAttribute("content")
    }
  }

  setupEventListeners() {
    // Login form
    this.handleLoginForm()

    // Register form
    this.handleRegisterForm()

    // Add to cart buttons
    this.handleAddToCart()

    // Remove from cart buttons
    this.handleRemoveFromCart()

    // Profile edit form
    this.handleProfileEdit()

    // Change password form
    this.handleChangePassword()

    // Search form
    this.handleSearchForm()

    // Category navigation
    this.handleCategoryNavigation()

    // Initialize product carousels
    this.initProductCarousels()
  }

  showLoading() {
    const spinner = document.getElementById("loadingSpinner")
    if (spinner) {
      spinner.style.display = "flex"
    }
  }

  hideLoading() {
    const spinner = document.getElementById("loadingSpinner")
    if (spinner) {
      spinner.style.display = "none"
    }
  }

  showMessage(message, type = "info") {
    // Remove existing messages
    const existingMessages = document.querySelectorAll(".ajax-message")
    existingMessages.forEach((msg) => msg.remove())

    const messageDiv = document.createElement("div")
    messageDiv.className = `ajax-message ajax-message-${type}`
    messageDiv.innerHTML = `
            <span>${message}</span>
            <button class="close-btn" onclick="this.parentElement.remove()">×</button>
        `

    document.body.insertBefore(messageDiv, document.body.firstChild)

    // Auto remove after 5 seconds
    setTimeout(() => {
      if (messageDiv.parentNode) {
        messageDiv.remove()
      }
    }, 5000)
  }

  handleLoginForm() {
    const loginForm = document.querySelector('form[action="/login"]')
    if (!loginForm) return

    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault()

      const formData = new FormData(loginForm)
      const email = formData.get("email")
      const password = formData.get("password")

      // Client-side validation
      if (!email || !password) {
        this.showMessage("Vui lòng nhập đầy đủ email và mật khẩu!", "error")
        return
      }

      if (!this.validateEmail(email)) {
        this.showMessage("Định dạng email không hợp lệ!", "error")
        return
      }

      this.showLoading()

      try {
        const response = await fetch("/login", {
          method: "POST",
          body: formData,
        })

        const result = await response.text()

        if (response.ok && result.includes("Chào mừng")) {
          this.showMessage("Đăng nhập thành công!", "success")
          setTimeout(() => {
            window.location.href = "/"
          }, 1000)
        } else {
          // Extract error message from response
          const errorMatch = result.match(/class="alert[^"]*"[^>]*>([^<]+)/)
          const errorMessage = errorMatch ? errorMatch[1] : "Email hoặc mật khẩu không đúng!"
          this.showMessage(errorMessage, "error")
        }
      } catch (error) {
        this.showMessage("Lỗi kết nối! Vui lòng thử lại.", "error")
      } finally {
        this.hideLoading()
      }
    })
  }

  handleRegisterForm() {
    const registerForm = document.querySelector('form[action="/register"]')
    if (!registerForm) return

    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault()

      const formData = new FormData(registerForm)

      // Client-side validation
      if (!this.validateRegisterForm(formData)) {
        return
      }

      this.showLoading()

      try {
        const response = await fetch("/register", {
          method: "POST",
          body: formData,
        })

        const result = await response.text()

        if (response.ok && result.includes("thành công")) {
          this.showMessage("Đăng ký thành công! Vui lòng đăng nhập.", "success")
          setTimeout(() => {
            window.location.href = "/loginForm"
          }, 1500)
        } else {
          const errorMatch = result.match(/class="alert[^"]*"[^>]*>([^<]+)/)
          const errorMessage = errorMatch ? errorMatch[1] : "Có lỗi xảy ra khi đăng ký!"
          this.showMessage(errorMessage, "error")
        }
      } catch (error) {
        this.showMessage("Lỗi kết nối! Vui lòng thử lại.", "error")
      } finally {
        this.hideLoading()
      }
    })
  }

  handleAddToCart() {
    // Handle add to cart buttons
    document.addEventListener("click", async (e) => {
      if (e.target.matches(".add-to-cart-btn") || e.target.closest(".add-to-cart-btn")) {
        e.preventDefault()

        const button = e.target.matches(".add-to-cart-btn") ? e.target : e.target.closest(".add-to-cart-btn")
        const productId = button.dataset.productId || new URLSearchParams(button.href.split("?")[1]).get("productId")

        if (!productId) {
          this.showMessage("Không tìm thấy thông tin sản phẩm!", "error")
          return
        }

        this.showLoading()

        try {
          const response = await fetch(`/addToCart?productId=${productId}`)
          const result = await response.text()

          if (response.ok) {
            if (result.includes("Đã thêm")) {
              this.showMessage("Đã thêm sản phẩm vào giỏ hàng!", "success")
              this.updateCartCount()
            } else if (result.includes("đăng nhập")) {
              this.showMessage("Vui lòng đăng nhập để thêm sản phẩm!", "warning")
              setTimeout(() => {
                window.location.href = "/loginForm"
              }, 1500)
            } else {
              const errorMatch = result.match(/class="alert[^"]*"[^>]*>([^<]+)/)
              const errorMessage = errorMatch ? errorMatch[1] : "Không thể thêm sản phẩm vào giỏ hàng!"
              this.showMessage(errorMessage, "error")
            }
          }
        } catch (error) {
          this.showMessage("Lỗi kết nối! Vui lòng thử lại.", "error")
        } finally {
          this.hideLoading()
        }
      }
    })
  }

  handleRemoveFromCart() {
    document.addEventListener("click", async (e) => {
      if (e.target.matches(".remove-from-cart-btn") || e.target.closest(".remove-from-cart-btn")) {
        e.preventDefault()

        const button = e.target.matches(".remove-from-cart-btn") ? e.target : e.target.closest(".remove-from-cart-btn")
        const productId = button.dataset.productId || new URLSearchParams(button.href.split("?")[1]).get("productId")

        if (!confirm("Bạn có chắc muốn xóa sản phẩm này khỏi giỏ hàng?")) {
          return
        }

        this.showLoading()

        try {
          const response = await fetch(`/removeFromCart?productId=${productId}`)
          const result = await response.text()

          if (response.ok) {
            this.showMessage("Đã xóa sản phẩm khỏi giỏ hàng!", "success")
            this.updateCartCount()
            // Remove product row from cart table
            const productRow = button.closest("tr") || button.closest(".product-item")
            if (productRow) {
              productRow.remove()
            }
            // Update total price
            this.updateCartTotal()
          }
        } catch (error) {
          this.showMessage("Lỗi kết nối! Vui lòng thử lại.", "error")
        } finally {
          this.hideLoading()
        }
      }
    })
  }

  handleProfileEdit() {
    const profileForm = document.querySelector('form[action*="/account/profile/edit"]')
    if (!profileForm) return

    profileForm.addEventListener("submit", async (e) => {
      e.preventDefault()

      const formData = new FormData(profileForm)

      // Client-side validation
      if (!formData.get("firstName") || !formData.get("lastName")) {
        this.showMessage("Họ và tên không được để trống!", "error")
        return
      }

      this.showLoading()

      try {
        const response = await fetch("/account/profile/edit", {
          method: "POST",
          body: formData,
        })

        const result = await response.text()

        if (response.ok && result.includes("thành công")) {
          this.showMessage("Cập nhật thông tin thành công!", "success")
        } else {
          const errorMatch = result.match(/class="alert[^"]*"[^>]*>([^<]+)/)
          const errorMessage = errorMatch ? errorMatch[1] : "Có lỗi khi cập nhật thông tin!"
          this.showMessage(errorMessage, "error")
        }
      } catch (error) {
        this.showMessage("Lỗi kết nối! Vui lòng thử lại.", "error")
      } finally {
        this.hideLoading()
      }
    })
  }

  handleChangePassword() {
    const passwordForm = document.querySelector('form[action*="/changePassword"]')
    if (!passwordForm) return

    passwordForm.addEventListener("submit", async (e) => {
      e.preventDefault()

      const formData = new FormData(passwordForm)
      const newPassword = formData.get("newpassword")
      const confirmPassword = formData.get("confirmpassword")

      // Client-side validation
      if (newPassword !== confirmPassword) {
        this.showMessage("Mật khẩu mới và xác nhận không khớp!", "error")
        return
      }

      if (newPassword.length < 6) {
        this.showMessage("Mật khẩu mới phải có ít nhất 6 ký tự!", "error")
        return
      }

      this.showLoading()

      try {
        const response = await fetch("/account/profile/changePassword", {
          method: "POST",
          body: formData,
        })

        const result = await response.text()

        if (response.ok && result.includes("thành công")) {
          this.showMessage("Đổi mật khẩu thành công!", "success")
          passwordForm.reset()
        } else {
          const errorMatch = result.match(/class="alert[^"]*"[^>]*>([^<]+)/)
          const errorMessage = errorMatch ? errorMatch[1] : "Có lỗi khi đổi mật khẩu!"
          this.showMessage(errorMessage, "error")
        }
      } catch (error) {
        this.showMessage("Lỗi kết nối! Vui lòng thử lại.", "error")
      } finally {
        this.hideLoading()
      }
    })
  }

  handleSearchForm() {
    const searchForm = document.querySelector("form")
    const searchBox = document.getElementById("searchBox")

    if (!searchForm || !searchBox) return

    searchForm.addEventListener("submit", async (e) => {
      const searchQuery = searchBox.value.trim()
      if (!searchQuery) {
        e.preventDefault()
        this.showMessage("Vui lòng nhập từ khóa tìm kiếm!", "warning")
        return
      }
    })

    // Auto-complete functionality
    let searchTimeout
    searchBox.addEventListener("input", (e) => {
      clearTimeout(searchTimeout)
      const query = e.target.value.trim()

      if (query.length >= 2) {
        searchTimeout = setTimeout(() => {
          this.showSearchSuggestions(query)
        }, 300)
      } else {
        this.hideSearchSuggestions()
      }
    })
  }

  handleCategoryNavigation() {
    document.addEventListener("click", async (e) => {
      if (e.target.matches('a[href*="/displayCategory"]')) {
        e.preventDefault()

        const categoryUrl = e.target.href
        this.showLoading()

        try {
          const response = await fetch(categoryUrl)
          const result = await response.text()

          if (response.ok) {
            const parser = new DOMParser()
            const doc = parser.parseFromString(result, "text/html")
            const newContent = doc.querySelector(".display")

            if (newContent) {
              document.querySelector(".display").innerHTML = newContent.innerHTML
              // Update URL without page reload
              history.pushState(null, "", categoryUrl)

              // Re-initialize carousels after content update
              this.initProductCarousels()
            }
          }
        } catch (error) {
          this.showMessage("Lỗi khi tải danh mục!", "error")
        } finally {
          this.hideLoading()
        }
      }
    })
  }

  async updateCartCount() {
    try {
      const response = await fetch("/cart")
      const result = await response.text()

      const parser = new DOMParser()
      const doc = parser.parseFromString(result, "text/html")
      const cartCount = doc.querySelector("#kart a")?.textContent.match(/\d+/)

      if (cartCount) {
        const cartElement = document.querySelector("#kart a")
        if (cartElement) {
          cartElement.innerHTML = cartElement.innerHTML.replace(/\d+/, cartCount[0])
        }
      }
    } catch (error) {
      console.error("Error updating cart count:", error)
    }
  }

  updateCartTotal() {
    const priceElements = document.querySelectorAll(".product-price")
    let total = 0

    priceElements.forEach((element) => {
      const price = Number.parseFloat(element.textContent.replace(/[^\d.]/g, ""))
      if (!isNaN(price)) {
        total += price
      }
    })

    const totalElement = document.querySelector(".cart-total")
    if (totalElement) {
      totalElement.textContent = `${total.toLocaleString()} VND`
    }
  }

  showSearchSuggestions(query) {
    // Create suggestions dropdown
    let suggestionsDiv = document.getElementById("searchSuggestions")
    if (!suggestionsDiv) {
      suggestionsDiv = document.createElement("div")
      suggestionsDiv.id = "searchSuggestions"
      suggestionsDiv.className = "search-suggestions"
      document.getElementById("searchBox").parentNode.appendChild(suggestionsDiv)
    }

    // Mock suggestions - in real app, fetch from server
    const suggestions = [
      "Điện thoại iPhone",
      "Laptop Dell",
      "Tai nghe Bluetooth",
      "Máy tính bảng",
      "Đồng hồ thông minh",
    ].filter((item) => item.toLowerCase().includes(query.toLowerCase()))

    if (suggestions.length > 0) {
      suggestionsDiv.innerHTML = suggestions
        .map(
          (suggestion) =>
            `<div class="suggestion-item" onclick="document.getElementById('searchBox').value='${suggestion}'">${suggestion}</div>`,
        )
        .join("")
      suggestionsDiv.style.display = "block"
    } else {
      this.hideSearchSuggestions()
    }
  }

  hideSearchSuggestions() {
    const suggestionsDiv = document.getElementById("searchSuggestions")
    if (suggestionsDiv) {
      suggestionsDiv.style.display = "none"
    }
  }

  validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  validateRegisterForm(formData) {
    const email = formData.get("email")
    const password = formData.get("password")
    const cpassword = formData.get("cpassword")
    const firstName = formData.get("firstName")
    const lastName = formData.get("lastName")

    if (!email || !password || !firstName || !lastName) {
      this.showMessage("Vui lòng điền đầy đủ thông tin bắt buộc!", "error")
      return false
    }

    if (!this.validateEmail(email)) {
      this.showMessage("Email không hợp lệ!", "error")
      return false
    }

    if (password !== cpassword) {
      this.showMessage("Mật khẩu xác nhận không khớp!", "error")
      return false
    }

    if (password.length < 6) {
      this.showMessage("Mật khẩu phải có ít nhất 6 ký tự!", "error")
      return false
    }

    return true
  }

  // ===== CAROUSEL FUNCTIONALITY =====

  initProductCarousels() {
    const carousels = document.querySelectorAll(".product-carousel-container")

    carousels.forEach((carousel) => {
      // Khởi tạo carousel
      this.setupCarousel(carousel)

      // Thêm hiệu ứng hover
      this.addCarouselHoverEffects(carousel)

      // Thêm hỗ trợ touch
      this.addTouchSupport(carousel)
    })

    // Thêm hỗ trợ phím mũi tên
    this.addKeyboardSupport()

    // Xử lý resize
    this.handleCarouselResize()
  }

  setupCarousel(carousel) {
    const productCarousel = carousel.querySelector(".product-carousel")
    const prevButton = carousel.querySelector(".prev-button")
    const nextButton = carousel.querySelector(".next-button")
    const table = productCarousel.querySelector("table")

    if (!table || !prevButton || !nextButton) return

    // Lưu trữ dữ liệu carousel
    carousel.dataset.currentPosition = "0"

    // Số lượng sản phẩm hiển thị cùng lúc
    const visibleProducts = this.getVisibleProductCount()
    const totalProducts = table.querySelectorAll("#productName td").length
    const maxPosition = Math.max(0, totalProducts - visibleProducts)

    carousel.dataset.maxPosition = maxPosition.toString()

    // Cập nhật trạng thái nút
    this.updateCarouselButtonState(carousel)

    // Xử lý sự kiện khi click nút trước
    prevButton.addEventListener("click", () => {
      this.navigateCarousel(carousel, "prev")
    })

    // Xử lý sự kiện khi click nút tiếp theo
    nextButton.addEventListener("click", () => {
      this.navigateCarousel(carousel, "next")
    })
  }

  navigateCarousel(carousel, direction) {
    const currentPosition = Number.parseInt(carousel.dataset.currentPosition || "0")
    const maxPosition = Number.parseInt(carousel.dataset.maxPosition || "0")
    let newPosition = currentPosition

    if (direction === "prev" && currentPosition > 0) {
      newPosition = currentPosition - 1
    } else if (direction === "next" && currentPosition < maxPosition) {
      newPosition = currentPosition + 1
    } else {
      return // Không thay đổi vị trí
    }

    // Cập nhật vị trí mới
    carousel.dataset.currentPosition = newPosition.toString()

    // Cuộn đến vị trí mới
    this.scrollCarouselToPosition(carousel, newPosition)

    // Cập nhật trạng thái nút
    this.updateCarouselButtonState(carousel)

    // Thêm hiệu ứng chuyển động
    this.addCarouselTransitionEffect(carousel)
  }

  scrollCarouselToPosition(carousel, position) {
    const productCarousel = carousel.querySelector(".product-carousel")
    const table = productCarousel.querySelector("table")

    if (!table) return

    const tdWidth = table.querySelector("#productName td")?.offsetWidth || 0
    const scrollAmount = position * tdWidth

    // Sử dụng scrollTo với hiệu ứng mượt mà
    productCarousel.scrollTo({
      left: scrollAmount,
      behavior: "smooth",
    })
  }

  updateCarouselButtonState(carousel) {
    const prevButton = carousel.querySelector(".prev-button")
    const nextButton = carousel.querySelector(".next-button")
    const currentPosition = Number.parseInt(carousel.dataset.currentPosition || "0")
    const maxPosition = Number.parseInt(carousel.dataset.maxPosition || "0")

    if (prevButton) {
      prevButton.disabled = currentPosition <= 0
      prevButton.classList.toggle("disabled", prevButton.disabled)
    }

    if (nextButton) {
      nextButton.disabled = currentPosition >= maxPosition
      nextButton.classList.toggle("disabled", nextButton.disabled)
    }
  }

  getVisibleProductCount() {
    const width = window.innerWidth
    if (width < 768) return 1
    if (width < 1024) return 2
    return 3
  }

  addCarouselHoverEffects(carousel) {
    // Thêm hiệu ứng khi hover vào carousel
    carousel.addEventListener("mouseenter", () => {
      carousel.classList.add("hovered")
    })

    carousel.addEventListener("mouseleave", () => {
      carousel.classList.remove("hovered")
    })
  }

  addTouchSupport(carousel) {
    const productCarousel = carousel.querySelector(".product-carousel")
    if (!productCarousel) return

    let startX = 0
    let currentX = 0
    let isDragging = false

    productCarousel.addEventListener("touchstart", (e) => {
      startX = e.touches[0].clientX
      isDragging = true
    })

    productCarousel.addEventListener("touchmove", (e) => {
      if (!isDragging) return
      currentX = e.touches[0].clientX
      // Ngăn cuộn trang khi vuốt carousel
      e.preventDefault()
    })

    productCarousel.addEventListener("touchend", () => {
      if (!isDragging) return

      const diff = startX - currentX
      const threshold = 50 // Ngưỡng để xác định vuốt

      if (Math.abs(diff) > threshold) {
        if (diff > 0) {
          // Vuốt sang trái -> Hiển thị sản phẩm tiếp theo
          this.navigateCarousel(carousel, "next")
        } else {
          // Vuốt sang phải -> Hiển thị sản phẩm trước đó
          this.navigateCarousel(carousel, "prev")
        }
      }

      isDragging = false
    })
  }

  addKeyboardSupport() {
    // Thêm hỗ trợ phím mũi tên
    document.addEventListener("keydown", (e) => {
      // Chỉ xử lý khi người dùng đang tương tác với carousel
      const activeCarousel = document.querySelector(".product-carousel-container.hovered")
      if (!activeCarousel) return

      if (e.key === "ArrowLeft") {
        this.navigateCarousel(activeCarousel, "prev")
      } else if (e.key === "ArrowRight") {
        this.navigateCarousel(activeCarousel, "next")
      }
    })
  }

  handleCarouselResize() {
    // Xử lý khi thay đổi kích thước màn hình
    let resizeTimeout

    window.addEventListener("resize", () => {
      clearTimeout(resizeTimeout)

      resizeTimeout = setTimeout(() => {
        const carousels = document.querySelectorAll(".product-carousel-container")

        carousels.forEach((carousel) => {
          // Cập nhật số lượng sản phẩm hiển thị
          const visibleProducts = this.getVisibleProductCount()
          const table = carousel.querySelector(".product-carousel table")

          if (!table) return

          const totalProducts = table.querySelectorAll("#productName td").length
          const maxPosition = Math.max(0, totalProducts - visibleProducts)

          // Cập nhật maxPosition
          carousel.dataset.maxPosition = maxPosition.toString()

          // Đảm bảo vị trí hiện tại vẫn hợp lệ
          const currentPosition = Number.parseInt(carousel.dataset.currentPosition || "0")
          if (currentPosition > maxPosition) {
            carousel.dataset.currentPosition = maxPosition.toString()
            this.scrollCarouselToPosition(carousel, maxPosition)
          }

          // Cập nhật trạng thái nút
          this.updateCarouselButtonState(carousel)
        })
      }, 200) // Debounce để tránh gọi quá nhiều lần
    })
  }

  addCarouselTransitionEffect(carousel) {
    // Thêm hiệu ứng khi chuyển sản phẩm
    const table = carousel.querySelector("table")
    if (!table) return

    table.classList.add("transitioning")

    setTimeout(() => {
      table.classList.remove("transitioning")
    }, 500)
  }
}

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new AjaxHandler()
})
// Main JavaScript file for the website

document.addEventListener("DOMContentLoaded", () => {
  // Handle intro section hide/show
  const hideIntroBtn = document.getElementById("hideIntroBtn")
  const introSection = document.getElementById("introduction")

  if (hideIntroBtn && introSection) {
    hideIntroBtn.addEventListener("click", () => {
      introSection.classList.add("hidden")
      // Save state to localStorage
      localStorage.setItem("introHidden", "true")
    })

    // Check if intro was previously hidden
    if (localStorage.getItem("introHidden") === "true") {
      introSection.classList.add("hidden")
    }
  }

  // Add smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault()
      const target = document.querySelector(this.getAttribute("href"))
      if (target) {
        target.scrollIntoView({
          behavior: "smooth",
          block: "start",
        })
      }
    })
  })

  // Add loading animation for images
  const images = document.querySelectorAll('img[loading="lazy"]')
  images.forEach((img) => {
    img.addEventListener("load", function () {
      this.style.opacity = "1"
    })
  })

  // Handle carousel navigation if exists
  const carouselContainers = document.querySelectorAll(".product-carousel-container")
  carouselContainers.forEach((container) => {
    const prevBtn = container.querySelector(".prev-button")
    const nextBtn = container.querySelector(".next-button")
    const carousel = container.querySelector(".product-carousel")

    if (prevBtn && nextBtn && carousel) {
      let scrollAmount = 0
      const scrollStep = 300

      nextBtn.addEventListener("click", () => {
        scrollAmount += scrollStep
        carousel.scrollTo({
          left: scrollAmount,
          behavior: "smooth",
        })
      })

      prevBtn.addEventListener("click", () => {
        scrollAmount -= scrollStep
        if (scrollAmount < 0) scrollAmount = 0
        carousel.scrollTo({
          left: scrollAmount,
          behavior: "smooth",
        })
      })
    }
  })
})

// Add show intro button functionality (optional)
function showIntro() {
  const introSection = document.getElementById("introduction")
  if (introSection) {
    introSection.classList.remove("hidden")
    localStorage.removeItem("introHidden")
  }
}

// Utility function for smooth page transitions
function smoothTransition(url) {
  document.body.style.opacity = "0.8"
  setTimeout(() => {
    window.location.href = url
  }, 200)
}

// Add CSS styles for Ajax components
const ajaxStyles = `
<style>
#loadingSpinner {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 9999;
}

.spinner-overlay {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100%;
    color: white;
}

.spinner {
    width: 70px;
    text-align: center;
}

.spinner > div {
    width: 18px;
    height: 18px;
    background-color: #fff;
    border-radius: 100%;
    display: inline-block;
    animation: sk-bouncedelay 1.4s infinite ease-in-out both;
}

.spinner .bounce1 {
    animation-delay: -0.32s;
}

.spinner .bounce2 {
    animation-delay: -0.16s;
}

@keyframes sk-bouncedelay {
    0%, 80%, 100% {
        transform: scale(0);
    } 40% {
        transform: scale(1.0);
    }
}

.ajax-message {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 20px;
    border-radius: 5px;
    color: white;
    font-weight: bold;
    z-index: 10000;
    max-width: 400px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    animation: slideIn 0.3s ease-out;
}

.ajax-message-success {
    background-color: #4CAF50;
}

.ajax-message-error {
    background-color: #f44336;
}

.ajax-message-warning {
    background-color: #ff9800;
}

.ajax-message-info {
    background-color: #2196F3;
}

.ajax-message .close-btn {
    background: none;
    border: none;
    color: white;
    font-size: 20px;
    cursor: pointer;
    margin-left: 10px;
}

.search-suggestions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #ddd;
    border-top: none;
    max-height: 200px;
    overflow-y: auto;
    z-index: 1000;
    display: none;
}

.suggestion-item {
    padding: 10px;
    cursor: pointer;
    border-bottom: 1px solid #eee;
}

.suggestion-item:hover {
    background-color: #f5f5f5;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* Carousel transition effect */
table.transitioning {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    transform: scale(1.02);
}

/* Carousel hover effect */
.product-carousel-container.hovered .nav-button {
    opacity: 1;
}
</style>
`

// Inject styles
document.head.insertAdjacentHTML("beforeend", ajaxStyles)
