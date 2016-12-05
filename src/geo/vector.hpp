#ifndef VECTOR_HPP_DA39A3EE
#define VECTOR_HPP_DA39A3EE

#include <algorithm>
#include <array>
#include <initializer_list>

namespace geo {

	template< typename T, size_t N >
	struct Vector : std::array<T, N> {

		T &x() {
			static_assert( N > 0 );
			return (*this)[0];
		}
		T const &x() const {
			return x();
		}

		T &y() {
			static_assert( N > 1 );
			return (*this)[1];
		}
		T const &y() const {
			return y();
		}

		T &z() {
			static_assert( N > 2 );
			return (*this)[2];
		}
		T const &z() const {
			return z();
		}

		T &w() {
			static_assert( N > 3 );
			return (*this)[3];
		}
		T const &w() const {
			return w();
		}

		friend auto dot( Vector const &a, Vector const &b ) -> T {
			T sum();
			if constexpr ( N > 0 ) {
				for ( size_t i = 0; i < a.size(); ++i ) {
					sum += a[i] * b[i];
				}
			}
			return sum;
		}

	};

	template< typename ...T >
	auto makeVector( T &&...t ) {
		return Vector< std::common_type_t<T...>, sizeof...(T) >{
				std::forward<T>( t )... };
	}

	template< size_t N > using VectorF = Vector<float, N>;
	template< size_t N > using VectorD = Vector<double, N>;

	template< typename T > using Vector1 = Vector<T, 1>;
	template< typename T > using Vector2 = Vector<T, 2>;
	template< typename T > using Vector3 = Vector<T, 3>;
	template< typename T > using Vector4 = Vector<T, 4>;

	using VectorF1 = VectorF<1>;
	using VectorF2 = VectorF<2>;
	using VectorF3 = VectorF<3>;
	using VectorF4 = VectorF<4>;

	using VectorD1 = VectorD<1>;
	using VectorD2 = VectorD<2>;
	using VectorD3 = VectorD<3>;
	using VectorD4 = VectorD<4>;
}

#endif
